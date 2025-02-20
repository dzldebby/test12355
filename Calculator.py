import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog
import traceback
from analytics import (
    identify_user, 
    assign_variant, 
    track_calculation, 
    mp,
    MIXPANEL_ENABLED,
)
from streamlit_javascript import st_javascript
from user_agents import parse
from utils.data_processor import prepare_features, PRODUCT_MAPPING, save_user_data
from utils.model_handler import ProductRecommender
from train_initial_model import train_initial_model
import requests
import tempfile
import pickle

def calculate_bank_interest(deposit_amount, bank_info, bank_requirements):
    """Calculate interest based on the bank's tier structure and requirements"""
    total_interest = 0
    breakdown = []
    
    # In the add_tier function
    def add_tier(amount, rate, description=""):
        interest = amount * rate
        # Debug print
        # print(f"Adding tier: amount={amount}, rate={rate}, description={description}")
        breakdown.append({
            'amount_in_tier': float(amount),
            'tier_rate': float(rate),
            'tier_interest': interest,
            'monthly_interest': interest / 12,
            'description': str(description).strip() 
        })
        return interest

    if bank_info['bank'] == 'SC BonusSaver':
        # Get requirement thresholds from tiers
        salary_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'salary')
        spend_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'spend')
        min_salary = float(salary_tier['min_salary'])
        min_spend = float(spend_tier['min_spend'])
        
        # Always add base interest for total balance
        base_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'base')
        base_rate = float(str(base_tier['interest_rate']).strip('%')) / 100
        total_interest += add_tier(deposit_amount, base_rate, "Base Interest")
        
        # Cap bonus interest at $100,000
        eligible_amount = min(deposit_amount, 100000)
        
        # Add salary bonus if applicable
        if bank_requirements['has_salary'] and bank_requirements['salary_amount'] >= min_salary:
            rate = float(str(salary_tier['interest_rate']).strip('%')) / 100
            total_interest += add_tier(eligible_amount, rate, f"Salary Credit Bonus (>= ${min_salary:,.0f})")
        
        # Add spend bonus if applicable
        if bank_requirements['spend_amount'] >= min_spend:
            rate = float(str(spend_tier['interest_rate']).strip('%')) / 100
            total_interest += add_tier(eligible_amount, rate, f"Card Spend Bonus (>= ${min_spend:,.0f})")
        
        # Add investment bonus if applicable
        if bank_requirements['has_investments']:
            invest_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'invest')
            rate = float(str(invest_tier['interest_rate']).strip('%')) / 100
            total_interest += add_tier(eligible_amount, rate, "Investment Bonus (6 months)")
        
        # Add insurance bonus if applicable
        if bank_requirements['has_insurance']:
            insure_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'insure')
            rate = float(str(insure_tier['interest_rate']).strip('%')) / 100
            total_interest += add_tier(eligible_amount, rate, "Insurance Bonus (6 months)")
            
    elif bank_info['bank'] == 'UOB One':
        # Initialize total interest
        total_interest = 0
        
        # Check if minimum spend requirement is met
        has_spend = bank_requirements['spend_amount'] >= 500
        has_salary = bank_requirements['has_salary']
        has_giro = bank_requirements['giro_count'] >= 3
        
        if has_spend:
            # If minimum spend met, check for highest applicable bonus rate
            remaining_amount = deposit_amount
            
            # Check salary + spend first as it has highest rates
            if has_salary:
                tiers = [t for t in bank_info['tiers'] if t['requirement_type'] == 'salary']
                for tier in tiers:
                    amount_in_tier = min(remaining_amount, float(tier['cap_amount']))
                    if amount_in_tier <= 0:
                        break
                    rate = float(str(tier['interest_rate']).strip('%')) / 100
                    interest = amount_in_tier * rate
                    total_interest += interest
                    add_tier(amount_in_tier, rate,
                        f"Salary + Spend ({tier['balance_tier']})")
                    remaining_amount -= amount_in_tier
            
            # Then check GIRO + Spend
            elif has_giro:
                tiers = [t for t in bank_info['tiers'] if t['requirement_type'] == 'giro']
                for tier in tiers:
                    amount_in_tier = min(remaining_amount, float(tier['cap_amount']))
                    if amount_in_tier <= 0:
                        break
                    rate = float(str(tier['interest_rate']).strip('%')) / 100
                    interest = amount_in_tier * rate
                    total_interest += interest
                    add_tier(amount_in_tier, rate,
                        f"GIRO + Spend ({tier['balance_tier']})")
                    remaining_amount -= amount_in_tier
            
            # Finally apply spend only rates
            else:
                tiers = [t for t in bank_info['tiers'] if t['requirement_type'] == 'spend_only']
                for tier in tiers:
                    amount_in_tier = min(remaining_amount, float(tier['cap_amount']))
                    if amount_in_tier <= 0:
                        break
                    rate = float(str(tier['interest_rate']).strip('%')) / 100
                    interest = amount_in_tier * rate
                    total_interest += interest
                    add_tier(amount_in_tier, rate,
                        f"Spend Only ({tier['balance_tier']})")
                    remaining_amount -= amount_in_tier
        
        else:
            # If minimum spend not met, only apply base interest
            base_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'base')
            base_rate = float(str(base_tier['interest_rate']).strip('%')) / 100
            base_amount = min(deposit_amount, float(base_tier['cap_amount']))
            base_interest = base_amount * base_rate
            total_interest += base_interest
            add_tier(base_amount, base_rate, f"Base Interest ({base_tier['balance_tier']})")
    
    elif bank_info['bank'] == 'OCBC 360':
        # Always add base interest first for total amount
        base_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'base')
        base_rate = float(str(base_tier['interest_rate']).strip('%')) / 100
        total_interest = deposit_amount * base_rate
        add_tier(deposit_amount, base_rate, "Base Interest")
        
        # Get tiers for first $75k and next $25k
        first_75k = min(deposit_amount, 75000)
        next_25k = min(max(deposit_amount - 75000, 0), 25000)
        
        # Base calculations for each amount
        total_first_75k = 0
        total_next_25k = 0
        
        def process_ocbc_tier(tier_type, requirement_met):
            nonlocal total_first_75k, total_next_25k
            if requirement_met:
                tier_75k = next((t for t in bank_info['tiers'] if t['tier_type'] == tier_type and float(t['cap_amount']) == 75000), None)
                tier_25k = next((t for t in bank_info['tiers'] if t['tier_type'] == tier_type and float(t['cap_amount']) == 25000), None)
                
                if tier_75k:
                    rate = float(str(tier_75k['interest_rate']).strip('%')) / 100
                    interest_75k = first_75k * rate
                    total_first_75k += interest_75k
                    add_tier(first_75k, rate, f"{tier_75k['remarks']}")
                
                if tier_25k:
                    rate = float(str(tier_25k['interest_rate']).strip('%')) / 100
                    interest_25k = next_25k * rate
                    total_next_25k += interest_25k
                    add_tier(next_25k, rate, f"{tier_25k['remarks']}")
        
        # Check each bonus category
        # Salary bonus
        salary_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'salary')
        has_salary = bank_requirements['has_salary'] and bank_requirements['salary_amount'] >= float(salary_tier['min_salary'])
        process_ocbc_tier('salary', has_salary)
        
        # Save bonus (increased balance)
        process_ocbc_tier('save', bank_requirements.get('increased_balance', False))
        
        # Spend bonus
        spend_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'spend')
        has_spend = bank_requirements['spend_amount'] >= float(spend_tier['min_spend'])
        process_ocbc_tier('spend', has_spend)
        
        # Insurance bonus
        process_ocbc_tier('insure', bank_requirements.get('has_insurance', False))
        
        # Investment bonus
        process_ocbc_tier('invest', bank_requirements.get('has_investments', False))
        
        # Grow bonus
        process_ocbc_tier('grow', bank_requirements.get('grew_wealth', False))
        
        total_interest += total_first_75k + total_next_25k
    
    elif bank_info['bank'] == 'BOC SmartSaver':
        # Initialize total interest
        total_interest = 0
        remaining_amount = deposit_amount

        # Process base interest tiers
        base_tiers = [t for t in bank_info['tiers'] if t['tier_type'] == 'base']
        # Sort tiers by cap_amount to process in ascending order
        base_tiers = sorted(base_tiers, key=lambda x: float(x['cap_amount']))
        
        # Track previous tier cap for tier calculation
        prev_cap = 0
        for tier in base_tiers:
            cap = float(tier['cap_amount'])
            tier_size = cap - prev_cap
            amount_in_tier = min(max(0, remaining_amount - prev_cap), tier_size)
            
            if amount_in_tier <= 0:
                break
                
            rate = float(str(tier['interest_rate']).strip('%')) / 100
            interest = amount_in_tier * rate
            total_interest += interest
            add_tier(amount_in_tier, rate, f"Base Interest ({tier['balance_tier']})")
            prev_cap = cap
        
        # Add bonus interest based on requirements
        if deposit_amount >= 1500:  # Minimum balance requirement
            # Process salary credit bonus if applicable
            if bank_requirements.get('has_salary', False) and bank_requirements.get('salary_amount', 0) >= 2000:
                salary_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'salary')
                rate = float(str(salary_tier['interest_rate']).strip('%')) / 100
                bonus_amount = min(deposit_amount, float(salary_tier['cap_amount']))
                interest = bonus_amount * rate
                total_interest += interest
                add_tier(bonus_amount, rate, "Salary Credit Bonus (≥$2,000)")

            # Process wealth bonus if applicable
            if bank_requirements.get('has_insurance', False):
                wealth_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'wealth')
                rate = float(str(wealth_tier['interest_rate']).strip('%')) / 100
                bonus_amount = min(deposit_amount, float(wealth_tier['cap_amount']))
                interest = bonus_amount * rate
                total_interest += interest
                add_tier(bonus_amount, rate, "Wealth Bonus (Insurance)")
            
            # Process spend bonus if applicable
            spend_amount = bank_requirements.get('spend_amount', 0)
            if spend_amount >= 500:
                # Get appropriate spend tier based on amount
                spend_tiers = [t for t in bank_info['tiers'] if t['tier_type'] == 'spend']
                spend_tier = None
                if spend_amount >= 1500:
                    spend_tier = next(t for t in spend_tiers if t['balance_tier'] == '2')
                else:
                    spend_tier = next(t for t in spend_tiers if t['balance_tier'] == '1')
                
                rate = float(str(spend_tier['interest_rate']).strip('%')) / 100
                bonus_amount = min(deposit_amount, float(spend_tier['cap_amount']))
                interest = bonus_amount * rate
                total_interest += interest
                add_tier(bonus_amount, rate, f"Spend Bonus (${spend_amount:,.0f})")

            # Process payment bonus if applicable
            giro_count = bank_requirements.get('giro_count', 0)
            if giro_count >= 3:
                payment_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'payment')
                rate = float(str(payment_tier['interest_rate']).strip('%')) / 100
                bonus_amount = min(deposit_amount, float(payment_tier['cap_amount']))
                interest = bonus_amount * rate
                total_interest += interest
                add_tier(bonus_amount, rate, f"Payment Bonus ({giro_count} bill payments)")
    
    elif bank_info['bank'] == 'Chocolate':
        # First add base interest for total amount
        base_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'base')
        base_rate = float(str(base_tier['interest_rate']).strip('%')) / 100
        total_interest = deposit_amount * base_rate
        # add_tier(deposit_amount, base_rate, "Base Interest")
        
        # Then add bonus interest for tiered amounts
        first_20k = min(deposit_amount, 20000)
        next_30k = min(max(deposit_amount - 20000, 0), 30000)
        
        # First $20,000 at 3.60%
        first_20k = min(deposit_amount, 20000)
        first_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'base' and float(t['cap_amount']) == 20000)
        rate_20k = float(str(first_tier['interest_rate']).strip('%')) / 100
        interest_20k = first_20k * rate_20k
        total_interest = interest_20k
        add_tier(first_20k, rate_20k, "First $20,000")
        
        # Next $30,000 at 3.20%
        if deposit_amount > 20000:
            next_30k = min(deposit_amount - 20000, 30000)
            second_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'base' and float(t['cap_amount']) == 30000)
            rate_30k = float(str(second_tier['interest_rate']).strip('%')) / 100
            interest_30k = next_30k * rate_30k
            total_interest += interest_30k
            add_tier(next_30k, rate_30k, "Next $30,000")
    
    return {
        'total_interest': total_interest,
        'breakdown': breakdown
    }

def process_interest_rates(file_path='interest_rates.csv'):
    """Process interest rates from CSV file"""
    print("Starting to process interest rates...")
    df = pd.read_csv(file_path)
    print(f"Loaded CSV with {len(df)} rows")
    banks_data = {}
    
    # Group by bank
    for bank_name, bank_group in df.groupby('bank'):
        #print(f"\nProcessing bank: {bank_name}")
        try:
            # Initialize bank data
            banks_data[bank_name] = {
                'bank': bank_name,
                'tiers': []
            }
            
            # Process all tiers
            for _, row in bank_group.iterrows():
                try:
                    # Convert interest rate from percentage string to float
                    rate = float(str(row['interest_rate']).strip('%')) / 100
                    
                    tier = {
                        'tier_type': row['tier_type'],
                        'balance_tier': row['balance_tier'],
                        'interest_rate': row['interest_rate'],
                        'requirement_type': row['requirement_type'],
                        'min_spend': row['min_spend'],
                        'min_salary': row['min_salary'],
                        'giro_count': row['giro_count'],
                        'salary_credit': row['salary_credit'],
                        'cap_amount': row['cap_amount'],
                        'remarks': row['remarks']
                    }
                    
                    banks_data[bank_name]['tiers'].append(tier)
                    #print(f"Added tier: {tier}")
                    pass
                    
                except (ValueError, TypeError) as e:
                    pass
                    #print(f"Error processing tier: {e}")
            
            print(f"Successfully added {len(banks_data[bank_name]['tiers'])} tiers for {bank_name}")
                
        except Exception as e:
            #print(f"Error processing {bank_name}: {e}")
            import traceback
            traceback.print_exc()
    
    #print(f"\nFinished processing. Found {len(banks_data)} banks")
    return banks_data

def optimize_bank_distribution(total_amount, banks_data, user_requirements):
    print(f"\nOptimizing distribution for ${total_amount:,.2f}")
    
    # Initialize variables for top 3 solutions
    top_solutions = [
        {'distribution': {}, 'total_interest': 0, 'breakdown': {}, 'salary_bank': None},
        {'distribution': {}, 'total_interest': 0, 'breakdown': {}, 'salary_bank': None},
        {'distribution': {}, 'total_interest': 0, 'breakdown': {}, 'salary_bank': None}
    ]

    # Define maximum bonus interest caps for each bank
    bonus_caps = {
        'UOB One': 150000,
        'SC BonusSaver': 100000,
        'OCBC 360': 100000,
        'BOC SmartSaver': 100000,
        'Chocolate': 50000
    }

    # Create progress placeholders in Streamlit
    status_text = st.empty()
    progress_text = st.empty()
    best_found_text = st.empty()
    
    # Initialize counters
    total_scenarios = 0
    current_scenario = 0
    
    # Calculate total number of scenarios
    def calculate_total_scenarios(amount, num_banks):
        # Number of possible $5000 increments for each bank
        increments_per_bank = (amount // 5000) + 1
        # Total combinations considering all banks
        return increments_per_bank ** num_banks

    # Calculate approximate total scenarios
    if user_requirements['has_salary']:
        for salary_bank in ['SC BonusSaver', 'OCBC 360', 'BOC SmartSaver']:
            total_scenarios += calculate_total_scenarios(min(total_amount, bonus_caps[salary_bank]), 4)  # 4 other banks
    total_scenarios += calculate_total_scenarios(total_amount, 5)  # non-salary scenarios
    
    progress_text.write(f"Total scenarios to check: {total_scenarios:,}")

    def try_combination(amounts_dict, salary_bank):
        nonlocal current_scenario
        current_scenario += 1
        
        if current_scenario % 100 == 0:  # Update more frequently since we have fewer scenarios
            progress_text.write(f"Checking scenario {current_scenario:,} of {total_scenarios:,} ({(current_scenario/total_scenarios*100):.1f}%)")
        
        if abs(sum(amounts_dict.values()) - total_amount) > 5000:  # Increased tolerance for $5000 increments
            return
            
        total_interest = 0
        all_breakdowns = {}
        
        for bank, amount in amounts_dict.items():
            if amount > 0:
                bank_reqs = user_requirements.copy()
                if bank == 'UOB One':
                    bank_reqs['has_salary'] = user_requirements.get('has_salary', False)
                    bank_reqs['salary_amount'] = user_requirements.get('salary_amount', 0)
                else:
                    bank_reqs['has_salary'] = (bank == salary_bank) and user_requirements['has_salary']
                
                result = calculate_bank_interest(amount, banks_data[bank], bank_reqs)
                total_interest += result['total_interest']
                all_breakdowns[bank] = result['breakdown']
        
        for i in range(len(top_solutions)):
            if total_interest > top_solutions[i]['total_interest']:
                for j in range(len(top_solutions)-1, i, -1):
                    top_solutions[j] = top_solutions[j-1].copy()
                top_solutions[i] = {
                    'distribution': amounts_dict.copy(),
                    'total_interest': total_interest,
                    'breakdown': all_breakdowns,
                    'salary_bank': salary_bank
                }
                best_found_text.write(f"New best found: ${total_interest:,.2f} with {amounts_dict}")
                break

    def try_all_combinations(remaining_amount, remaining_banks, current_distribution, salary_bank):
        if not remaining_banks:
            if remaining_amount < 5000:  # If less than $5000 left, consider it a valid combination
                try_combination(current_distribution, salary_bank)
            return
        
        current_bank = remaining_banks[0]
        next_banks = remaining_banks[1:]
        
        # Try different amounts in $5000 increments
        max_amount = min(remaining_amount, bonus_caps[current_bank])
        for amount in range(0, max_amount + 5000, 5000):  # Include 0 to skip this bank
            if amount <= max_amount:
                new_distribution = current_distribution.copy()
                if amount > 0:  # Only add to distribution if amount > 0
                    new_distribution[current_bank] = amount
                try_all_combinations(remaining_amount - amount, next_banks, new_distribution, salary_bank)

    # Try all possible combinations
    all_banks = ['UOB One', 'SC BonusSaver', 'OCBC 360', 'BOC SmartSaver', 'Chocolate']
    
    # First try with salary credit
    if user_requirements['has_salary']:
        for salary_bank in ['SC BonusSaver', 'OCBC 360', 'BOC SmartSaver']:
            status_text.write(f"Trying combinations with salary credit to {salary_bank}...")
            non_salary_banks = [bank for bank in all_banks if bank != salary_bank]
            # Try salary bank first
            for amount in range(0, min(total_amount + 5000, bonus_caps[salary_bank] + 5000), 5000):
                if amount <= total_amount:
                    initial_distribution = {salary_bank: amount} if amount > 0 else {}
                    try_all_combinations(total_amount - amount, non_salary_banks, initial_distribution, salary_bank)
    
    # Then try without salary credit
    status_text.write("Trying combinations without salary credit...")
    try_all_combinations(total_amount, ['UOB One', 'SC BonusSaver', 'OCBC 360', 'BOC SmartSaver', 'Chocolate'], {}, None)

    status_text.write("Optimization complete!")
    progress_text.empty()  # Clear the progress counter
    best_found_text.empty()  # Clear the best found message
    
    # Display final results
    st.write("\n### Final Top 3 Solutions:")
    for i, solution in enumerate(top_solutions):
        if solution['total_interest'] > 0:
            st.write(f"\n**Scenario {i+1}:**")
            st.write(f"Distribution: {solution['distribution']}")
            st.write(f"Total Interest: ${solution['total_interest']:,.2f}")
            st.write(f"Salary Bank: {solution['salary_bank']}")
    
    return top_solutions

def format_number(n):
    return "{:,}".format(n)

def show_interest_rates_page(banks_data):
    st.title("Bank Interest Rates")
    st.write("Current interest rates and requirements for supported banks. Updated as of 16 Jan 2025.")
    
    # Convert banks_data dictionary to a list of records
    records = []
    for bank_name, bank_info in banks_data.items():
        for tier in bank_info['tiers']:
            tier['bank'] = bank_name  # Add bank name to each tier
            records.append(tier)
    
    # Convert to DataFrame
    interest_rates_df = pd.DataFrame(records)
    
    for bank in interest_rates_df['bank'].unique():
        st.header(f"{bank}")
        bank_data = interest_rates_df[interest_rates_df['bank'] == bank]
        
        # Create a formatted table for each bank
        cols = ['tier_type', 'balance_tier', 'interest_rate', 'requirement_type', 'remarks']
        display_df = bank_data[cols].copy()
        display_df.columns = ['Tier Type', 'Balance Tier', 'Interest Rate (%)', 'Requirement', 'Remarks']
        
        st.dataframe(display_df, hide_index=True)
        st.markdown("---")

# Set page config first
st.set_page_config(
    page_title="SmartSaverSG",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"  # Start collapsed for mobile
)

# Add CSS for responsive sidebar and mobile optimization
st.markdown("""
    <style>
    /* Mobile optimizations */
    @media (max-width: 768px) {
        /* Optimize spacing for mobile */
        .block-container {
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        /* Make sidebar narrower on mobile */
        [data-testid="stSidebar"] {
            width: 80vw !important;
            min-width: 200px !important;
            max-width: 300px !important;
        }
    }

    /* Reduce title padding */
    .block-container {
        padding-top: 1rem !important;
    }

    /* Additional title spacing adjustments */
    .stTitle {
        margin-top: -2rem;
    }

    /* Reduce padding between subheader and horizontal line */
    .stSubheader {
        margin-bottom: -1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

def streamlit_app():

    # Initialize session state for PC detection if not exists
    if 'is_session_pc' not in st.session_state:
        st.session_state.is_session_pc = True  # Default to PC view

    # Get user agent info with error handling
    try:
        ua_string = st_javascript("""window.navigator.userAgent;""")
        if ua_string is not None:
            user_agent = parse(ua_string)
            st.session_state.is_session_pc = user_agent.is_pc
    except Exception:
        # Keep the default PC view if there's any error
        pass

    try:
        # User identification
        user_id = identify_user()
        variant = assign_variant()

        # Track page view
        if MIXPANEL_ENABLED:
            mp.track(st.session_state.user_id, 'Page Viewed', {
                'page': 'main',
                'variant': variant
            })

        # Then: Load interest rates data
        banks_data = process_interest_rates()
        
        # Custom CSS for the header
        st.markdown(f"""
            <style>
            .main-header {{
                text-align: center;
                padding: 0.5rem 0;
            }}
            .main-header h1 {{
                color: var(--text-color, currentColor);
                font-size: {"3rem" if st.session_state.is_session_pc else "2.5rem"} !important;
                font-weight: 700 !important;
                margin-bottom: 0.1rem !important;
                line-height: 1.2 !important;
            }}
            .main-header h3 {{
                color: var(--text-color, currentColor);
                font-size: 1.5rem !important;
                font-weight: 400 !important;
                margin-bottom: 0.1rem !important;
                line-height: 1.2 !important;
                display: {"block" if st.session_state.is_session_pc else "none"} !important;
            }}
            .header-divider {{
                width: 100%;
                height: 3px;
                background: var(--text-color, currentColor);
                opacity: 0.7;
                margin: 1em 0;
                border: none;
                display: {"block" if st.session_state.is_session_pc else "none"} !important;
            }}
            </style>
            
            <div class="main-header">
                <h1>🏦 SmartSaverSG</h1>
                <h3>Maximize Your Savings with Bank Interest Calculator</h3>
            </div>
            <hr class="header-divider">
        """, unsafe_allow_html=True)
        
        try:

            col1, col2 = st.columns([1, 1])



            
            try:
                with col1:
                    # col 1 start # 

                    # Requirements Section
                    st.write("##### Step 1: Enter Amount")
                    # Add A/B test variations for the input interface
                    if variant == 'A':
                        # Variant A: Text input (original)
                        amount_str = st.text_input(
                            "Enter amount to calculate interest for ($):", 
                            value="10,000",
                            help="Enter amount with commas (e.g., 100,000)"
                        )
                        investment_amount = int(amount_str.replace(",", ""))
                        
                        # Track page view
                        if MIXPANEL_ENABLED:
                            mp.track(st.session_state.user_id, 'Savings Entered (Text Input)', {
                                'savings': amount_str,
                                'variant': variant
                            })

                    else:
                        # Variant B: Slider input
                        amount_str = st.slider(
                            "Select amount to calculate interest for ($)",
                            min_value=0,
                            max_value=1000000,
                            value=10000,
                            step=1000,
                            format="$%d"
                        )
                        investment_amount = int(amount_str)

                                        # Track page view
                        if MIXPANEL_ENABLED:
                            mp.track(st.session_state.user_id, 'Savings Entered (Slider)', {
                                'savings': amount_str,
                                'variant': variant
                            })


                    
                    # Basic Requirements
                    st.write("##### Step 2: Enter Basic & Optional Requirements")
                    
                    with st.expander("✅ Basic Requirements", expanded=True):
                        # Salary Credit
                        has_salary = st.toggle(
                            "Credit Salary of >SGD$3,000 to Bank Account",
                            help="Select this if your salary of >$3K is credited to your bank account monthly"
                        )
                        if has_salary:
                            # assume salary amount >2K
                            salary_amount = 3001
                            # st.caption(f"Selected Salary: ${format_number(salary_amount)}")
                        else:
                            salary_amount = 0
                            
                        # Create two columns for Card Spend and Bill Payments
                        spend_col, giro_col = st.columns(2)
                        
                        with spend_col:
                            # Card Spend
                            card_spend = st.number_input(
                                "Card Spend per Month ($)",
                                min_value=0,
                                value=500,
                                step=100,
                                format="%d"
                            )
                            st.caption(f"Selected Card Spend: ${format_number(card_spend)}")

                        with giro_col:
                            # Number of Bill Payments
                            giro_count = st.number_input(
                                "Number of Bill Payments / GIRO",
                                min_value=0,
                                max_value=10,
                                value=0,
                                step=1
                            )
                            st.caption(f"Selected Bill Payments: {giro_count}")

                    # Advanced Requirements
                    with st.expander("📈 Advanced Requirements (Optional)", expanded=False):
                        has_insurance = st.toggle(
                            "Have Insurance Products",
                            help="""Select this if you have purchased eligible insurance products from any of the following banks: Standard Chartered, OCBC 360 (min. S$2,000 annual insurance premium), BOC SmartSaver 
                                """
                        )
                        has_investments = st.toggle(
                            "Have Investments",
                            help="""Select this if you have any of the following eligible investments products from any of the following banks: Standard Chartered, OCBC 360"""
                        )
                        increased_balance = st.toggle(
                            "[OCBC-Specific] Increased Account Balance",
                            help="""OCBC 360: Min. S$500 increase from previous month"""
                        )
                        grew_wealth = st.toggle(
                            "[OCBC-Specific] Grew Wealth",
                            help="""OCBC 360: Maintain an average daily balance of at least S$200,000."""
                        )

                    # Create base requirements dictionary (moved outside tabs)
                    base_requirements = {
                        'has_salary': bool(has_salary and salary_amount >= 2000),
                        'salary_amount': salary_amount,
                        'spend_amount': card_spend,
                        'giro_count': giro_count,
                        'has_insurance': has_insurance,
                        'has_investments': has_investments,
                        'increased_balance': increased_balance,
                        'grew_wealth': grew_wealth
                    }

                    # Show links differently based on device type
                    if st.session_state.is_session_pc:
                        # Desktop view - show in columns
                        tutorial_col, method_col, rates_col, feedback_col = st.columns(4)
                        with tutorial_col:
                            st.markdown("[How to use the calculator 📚](Tutorial)")
                        with method_col:
                            st.markdown("[Calculation Methodology 📝](Methodology)")
                        with rates_col:
                            st.markdown("[What interest rates are used?](Interest_Rates)")
                        with feedback_col:
                            st.markdown("[Provide Feedback](Feedback)")
                    else:
                        # Mobile view - show in expander
                        with st.expander("📱 Quick Links", expanded=False):
                            st.markdown("[How to use the calculator 📚](Tutorial)")
                            st.markdown("[Calculation Methodology 📝](Methodology)")
                            st.markdown("[What interest rates are used?](Interest_Rates)")
                            st.markdown("[Provide Feedback](Feedback)")

   
                # col 1 end #

                # col 2 start #
                with col2:

                    # Create a more descriptive section for the two options
                    st.write("##### Step 3: Select your calculation method:")
                    
                    # Create tabs with clearer descriptions and icons
                    tab1, tab2 = st.tabs([
                        "🏦 Single Bank Calculator",
                        "🎯 Insurance Product Recommendation"
                    ])
                    
                    with tab1:
                        # Initialize the show_description state if it doesn't exist
                        if 'show_description' not in st.session_state:
                            st.session_state.show_description = True

                        # Button needs to be before the conditional display
                        calculate_clicked = st.button("Calculate Single Bank Interest", type="primary", key="single_bank_calc")
                        if calculate_clicked:
                            st.session_state.show_description = False
                            track_calculation('single_bank', investment_amount, base_requirements)

                            if MIXPANEL_ENABLED:
                                mp.track(st.session_state.user_id, 'Calculation Performed', {
                                    'type': 'single_bank',
                                    'amount': investment_amount,
                                    'has_salary': has_salary,
                                    'card_spend': card_spend,
                                    'giro_count': giro_count,
                                    'variant': variant
                                })

                            # Add this line to call the function when button is clicked
                            calculate_single_bank(investment_amount, base_requirements)  # Pass both parameters

                        if st.session_state.show_description:
                            st.markdown("""
                                **Calculate interest for a single bank account***""")
                            st.markdown(""" - See detailed breakdowns for each bank""", help="Banks included: Chocolate Financial, UOB One, SC BonusSaver, BOC SmartSaver, OCBC 360")
                            st.markdown(""" - Compare base rates and bonus interest""")

                        if calculate_clicked:
                            with st.spinner("Calculating interest rates..."):
                                # Calculate and display results for each bank
                                bank_results = []
                                for bank_name in ["UOB One", "SC BonusSaver", "OCBC 360", "BOC SmartSaver", "Chocolate"]:
                                    bank_reqs = base_requirements.copy()
                                    
                                    # Special handling for UOB One
                                    if bank_name == 'UOB One':
                                        bank_reqs['has_salary'] = base_requirements.get('has_salary', False)
                                        bank_reqs['salary_amount'] = base_requirements.get('salary_amount', 0)
                                    
                                    results = calculate_bank_interest(
                                        investment_amount, 
                                        banks_data[bank_name], 
                                        bank_reqs
                                    )
                                    bank_results.append({
                                        'bank': bank_name,
                                        'monthly_interest': results['total_interest']/12,
                                        'annual_interest': results['total_interest'],
                                        'breakdown': results['breakdown']
                                    })
                                
                                # Sort banks by interest rate (highest to lowest)
                                bank_results.sort(key=lambda x: x['annual_interest'], reverse=True)
                                
                                # Display Optimal Bank First
                                optimal_bank = bank_results[0]
                                st.success(f"🏆 Optimal Choice: **{optimal_bank['bank']}** offers the highest interest rate!")
                                
                                st.metric("Monthly Interest", f"${optimal_bank['monthly_interest']:,.2f}")
                                st.metric("Annual Interest", f"${optimal_bank['annual_interest']:,.2f}")

                                
                                # Show breakdown for optimal bank
                                if optimal_bank['breakdown']:
                                    st.write("Interest Breakdown:")
                                    for tier in optimal_bank['breakdown']:
                                        try:
                                            # Convert all values to basic Python types first
                                            amount_val = float(tier['amount_in_tier'])
                                            rate_val = float(tier['tier_rate'])
                                            desc_val = str(tier['description']).strip()
                                            
                                            # Build string piece by piece
                                            bullet = "•"
                                            amount_str = "${:,.2f}".format(amount_val)
                                            rate_str = "{:.2f}%".format(rate_val * 100)
                                            
                                            # Combine with explicit spaces
                                            line = f"{bullet} {amount_str} at {rate_str} - {desc_val}"
                                            
                                            # Display using text
                                            st.text(line)
                                            
                                        except Exception as e:
                                            st.error(f"Error formatting tier {i}: {str(e)}")
                                    st.markdown("[See section below for more details →](#details-of-all-banks)")
                                
                                # Divider between optimal and all results
                                st.markdown("---")
                                
                                # Display All Bank Results
                                st.write("### Details of all banks")


                                # Define bank URLs
                                bank_urls = {
                                    "UOB One": "https://www.uob.com.sg/personal/save/chequeing/one-account.page",
                                    "OCBC 360": "https://www.ocbc.com/personal-banking/deposits/360-account",
                                    "SC BonusSaver": "https://www.sc.com/sg/save/current-accounts/bonussaver/",
                                    "BOC SmartSaver": "https://www.bankofchina.com/sg/pbservice/pb1/202212/t20221230_22348761.html",
                                    "Chocolate": "https://www.chocolatefinance.com/#Benefits"
                                }
                                


                                for result in bank_results:
                                    with st.expander(f"{result['bank']} Details", expanded=False):
                                        # Create two columns for Monthly and Annual Interest
                                        st.metric("Monthly Interest", f"${result['monthly_interest']:,.2f}")
                                        st.metric("Annual Interest", f"${result['annual_interest']:,.2f}")

                                                                        # Add bank URL if available
                                    
                                        # Show breakdown with fixed formatting
                                        if result['breakdown']:
                                            st.write("Interest Breakdown:")
                                            for tier in result['breakdown']:
                                                try:
                                                    # Convert all values to basic Python types first
                                                    amount_val = float(tier['amount_in_tier'])
                                                    rate_val = float(tier['tier_rate'])
                                                    desc_val = str(tier['description']).strip()
                                                    
                                                    # Build string piece by piece
                                                    bullet = "•"
                                                    amount_str = "${:,.2f}".format(amount_val)
                                                    rate_str = "{:.2f}%".format(rate_val * 100)
                                                    
                                                    # Combine with explicit spaces
                                                    line = f"{bullet} {amount_str} at {rate_str} - {desc_val}"
                                                    
                                                    # Display using text
                                                    st.text(line)
                                                    
                                                except Exception as e:
                                                    st.error(f"Error formatting tier {i}: {str(e)}")

                                                                    
                                        if result['bank'] == "Chocolate":
                                            st.write("Notes:")
                                            st.text("• Chocolate Finance targets 3% p.a. on any amount above $50K, but since this is only a target and not guaranteed, it has not been included in the calculation.")                

                                        if result['bank'] == "OCBC 360":
                                            st.write("Notes:")
                                            st.text("• OCBC's website calculator may show slightly different results because they calculate interest based on a 31-day month.")                

                                        if result['bank'] == "UOB One":
                                            st.write("Notes:")
                                            st.text("• There might be a further annual cash rebate of S$200. This has not been included in the calculations")  

                                        if result['bank'] in bank_urls:
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.markdown(f"🔍 Verify by visiting [{result['bank']}'s website →]({bank_urls[result['bank']]})")
                                            with col2:
                                                st.markdown("📝 Calculations look wrong? [Provide feedback →](/Feedback)")


                                # # Get product recommendation
                                # st.write("### 🔍 Product Recommendation Debug")
                                # st.write("Attempting to get product recommendation...")
                                
                                # recommender = ProductRecommender()
                                # st.write("✓ Created recommender instance")
                                
                                # model_loaded = recommender.load_model()
                                # st.write(f"✓ Model loaded: {model_loaded}")
                                
                                # if model_loaded:
                                #     user_data = prepare_features({
                                #         'savings_amount': float(investment_amount),
                                #         'salary_above_3k': float(base_requirements['salary_amount']) >= 3000,
                                #         'monthly_card_spend': float(base_requirements['spend_amount']),
                                #         'num_giro_payments': int(base_requirements['giro_count']),
                                #         'has_insurance': bool(base_requirements['has_insurance']),
                                #         'has_investments': bool(base_requirements['has_investments']),
                                #         'increased_balance': bool(base_requirements.get('increased_balance', False)),
                                #         'high_balance': float(investment_amount) >= 200000
                                #     })
                                #     st.write("✓ Prepared user data:", user_data)
                                    
                                #     prediction, probabilities, explanations = recommender.predict(user_data)
                                #     st.write(f"✓ Got prediction: {prediction}")
                                #     st.write(f"✓ Got probabilities: {probabilities}")
                                #     st.write(f"✓ Got explanations: {explanations}")
                                    
                                #     try:
                                #         total_records = save_user_data(user_data, prediction)
                                #         st.write(f"✓ Saved data. Total records: {total_records}")
                                #         if total_records > 0 and total_records % 5 == 0:
                                #             st.write("Training initial model...")
                                #             train_initial_model()
                                #     except Exception as e:
                                #         st.error(f"🚨 Unable to save recommendation data: {str(e)}")
                                #         st.write("Save error details:", str(e))
                                    
                                #     st.write("---")
                                #     st.write("### 🎯 Product Recommendation")
                                #     st.success(f"Based on your profile, we recommend: **{PRODUCT_MAPPING[prediction]}**")
                                    
                                #     with st.expander("View Recommendation Details", expanded=True):
                                #         # Show confidence scores
                                #         st.write("#### 📊 Confidence Scores")
                                #         for product_id, prob in enumerate(probabilities):
                                #             st.write(f"- {PRODUCT_MAPPING[product_id]}: {prob:.2%}")
                                        
                                #         # Show feature importance explanations
                                #         if explanations:
                                #             st.write("\n#### 🔍 Key Factors")
                                #             st.write("These factors influenced our recommendation:")
                                            
                                #             for exp in explanations:
                                #                 feature = exp['feature'].replace('_', ' ').title()
                                #                 value = exp['value']
                                #                 importance = exp['importance']
                                                
                                #                 # Create a more natural explanation
                                #                 if feature == 'Savings Amount':
                                #                     detail = f"Your savings amount of ${value:,.2f}"
                                #                 elif feature == 'Monthly Card Spend':
                                #                     detail = f"Your monthly card spend of ${value:,.2f}"
                                #                 elif feature == 'Num Giro Payments':
                                #                     detail = f"You have {int(value)} GIRO payments"
                                #                 elif feature == 'Has Insurance':
                                #                     detail = "You already have insurance" if value else "You don't have insurance yet"
                                #                 elif feature == 'Has Investments':
                                #                     detail = "You have existing investments" if value else "You don't have investments yet"
                                #                 elif feature == 'Increased Balance':
                                #                     detail = "Your balance has increased" if value else "Your balance hasn't increased"
                                #                 elif feature == 'High Balance':
                                #                     detail = "You have a high balance" if value else "You have a moderate balance"
                                #                 elif feature == 'Salary Above 3k':
                                #                     detail = "Your salary is above $3,000" if value else "Your salary is below $3,000"
                                                
                                #                 # Show explanation with importance
                                #                 importance_width = min(100, int(abs(importance) * 100))
                                #                 st.write(
                                #                     f"""<div style='display: flex; align-items: center; margin-bottom: 10px;'>
                                #                         <div style='flex: 1;'>{detail}</div>
                                #                         <div style='width: 100px; background: #f0f2f6; height: 10px; border-radius: 5px;'>
                                #                             <div style='width: {importance_width}%; background: #00c853; height: 100%; border-radius: 5px;'></div>
                                #                         </div>
                                #                     </div>""",
                                #                     unsafe_allow_html=True
                                #                 )
                                #         else:
                                #             st.warning("No explanation factors available")

                    with tab2:
                        st.write("### 🎯 Insurance Product Recommendation")
                        st.write("Based on your financial profile from Step 1, here's our insurance recommendation.")
                        
                        recommend_clicked = st.button("Get Recommendation", type="primary")
                        
                        if recommend_clicked:
                            try:
                                # Use values from Step 1
                                savings_amount = investment_amount  # From Step 1
                                monthly_spend = base_requirements['spend_amount']  # From Step 1
                                has_insurance = base_requirements.get('has_insurance', 0)  # From Step 1
                                
                                # Use raw GitHub URL
                                github_url = "https://raw.githubusercontent.com/dzldebby/test12355/7ad19457642cbae6579ba4a3cccd843006819cc0/models/insurance_model.pkl"
                                
                                # Download and load model
                                response = requests.get(github_url)
                                
                                if response.status_code == 200:
                                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                                        tmp_file.write(response.content)
                                        tmp_file.flush()
                                        
                                        with open(tmp_file.name, 'rb') as f:
                                            model_data = pickle.load(f)
                                            
                                        model = model_data['model']
                                        feature_names = model_data['feature_names']
                                        target_names = model_data['target_names']
                                        
                                        # Prepare features
                                        features = np.array([[
                                            float(savings_amount),
                                            float(monthly_spend),
                                            float(has_insurance)
                                        ]])
                                        
                                        # Get prediction and probabilities
                                        prediction = model.predict(features)[0]
                                        probabilities = model.predict_proba(features)[0]
                                        
                                        # Display recommendation
                                        recommended_product = target_names[prediction]
                                        st.success(f"✨ Recommended Insurance Product: **{recommended_product}**")
                                        
                                        # Display confidence scores
                                        st.write("#### Confidence Scores:")
                                        for product_id, prob in enumerate(probabilities):
                                            product_name = target_names[product_id]
                                            progress_width = int(prob * 100)
                                            st.write(
                                                f"""<div style='display: flex; align-items: center; margin-bottom: 10px;'>
                                                    <div style='width: 200px;'>{product_name}</div>
                                                    <div style='flex-grow: 1; background: #f0f2f6; height: 20px; border-radius: 10px;'>
                                                        <div style='width: {progress_width}%; background: #00c853; height: 100%; border-radius: 10px;'></div>
                                                    </div>
                                                    <div style='margin-left: 10px;'>{prob:.1%}</div>
                                                </div>""",
                                                unsafe_allow_html=True
                                            )
                                        
                                        # Display input features
                                        st.write("\n#### Based on your profile from Step 1:")
                                        st.write(f"• Savings Amount: ${savings_amount:,.2f}")
                                        st.write(f"• Monthly Card Spend: ${monthly_spend:,.2f}")
                                        st.write(f"• Has Existing Insurance: {'Yes' if has_insurance else 'No'}")
                                        
                                else:
                                    st.error("Unable to load insurance recommendation model")
                                    
                            except Exception as e:
                                st.error("Error generating insurance recommendation")

            # This is within col1 already
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.error(traceback.format_exc())

        # This closes the first try block within the 2-column layout        
        except Exception as e:
            # Handle UI-specific errors
            st.error(f"Error: {str(e)}")
            st.error(traceback.format_exc())

    # This belongs to the user id try, not part of the scope
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.error(traceback.format_exc())  

def optimize_spend_allocation(total_spend, banks_data, deposit_amounts, base_requirements):
    """
    Optimize credit card spend allocation across banks
    Returns the best spend allocation and corresponding interest
    """
    # Minimum spend requirements for each bank
    min_spends = {
        'UOB One': 500,
        'SC BonusSaver': 1000,
        'OCBC 360': 500,
        'BOC SmartSaver': 500
    }
    
    best_allocation = {}
    best_total_interest = 0
    best_breakdown = {}
    
    def try_allocation(remaining_spend, remaining_banks, current_allocation):
        nonlocal best_allocation, best_total_interest, best_breakdown
        
        # Base case: no more spend to allocate or no more banks
        if not remaining_banks or remaining_spend < min(min_spends.values()):
            # Calculate total interest with current allocation
            total_interest = 0
            interest_breakdown = {}
            
            for bank, spend in current_allocation.items():
                bank_reqs = base_requirements.copy()
                bank_reqs['spend_amount'] = spend
                
                # Special handling for UOB One
                if bank == 'UOB One':
                    bank_reqs['has_salary'] = base_requirements.get('has_salary', False)
                    bank_reqs['salary_amount'] = base_requirements.get('salary_amount', 0)
                
                result = calculate_bank_interest(
                    deposit_amounts.get(bank, 0), 
                    banks_data[bank], 
                    bank_reqs
                )
                total_interest += result['total_interest']
                interest_breakdown[bank] = result
            
            if total_interest > best_total_interest:
                best_allocation = current_allocation.copy()
                best_total_interest = total_interest
                best_breakdown = interest_breakdown
            return
        
        # Try allocating spend to next bank
        current_bank = remaining_banks[0]
        min_spend = min_spends[current_bank]
        
        # Try skipping this bank
        try_allocation(
            remaining_spend,
            remaining_banks[1:],
            current_allocation
        )
        
        # Try allocating minimum spend to this bank
        if remaining_spend >= min_spend:
            new_allocation = current_allocation.copy()
            new_allocation[current_bank] = min_spend
            try_allocation(
                remaining_spend - min_spend,
                remaining_banks[1:],
                new_allocation
            )
            
            # For BOC SmartSaver, try higher tier if possible
            if current_bank == 'BOC SmartSaver' and remaining_spend >= 1500:
                new_allocation[current_bank] = 1500
                try_allocation(
                    remaining_spend - 1500,
                    remaining_banks[1:],
                    new_allocation
                )
    
    # Start optimization with all banks
    eligible_banks = [bank for bank in min_spends.keys() 
                     if bank in deposit_amounts and deposit_amounts[bank] > 0]
    try_allocation(total_spend, eligible_banks, {})
    
    return best_allocation, best_total_interest, best_breakdown

def calculate_single_bank(investment_amount, base_requirements):
    st.write("---")
    st.write("### 🎯 Insurance Recommendation")
    
    try:
        # Use raw GitHub URL
        github_url = "https://raw.githubusercontent.com/dzldebby/test12355/7ad19457642cbae6579ba4a3cccd843006819cc0/models/insurance_model.pkl"
        
        # Download and load model
        response = requests.get(github_url)
        
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    model_data = pickle.load(f)
                    
                model = model_data['model']
                feature_names = model_data['feature_names']
                target_names = model_data['target_names']
                
                # Prepare features
                features = np.array([[
                    float(investment_amount),
                    float(base_requirements['spend_amount']),
                    float(base_requirements.get('has_insurance', 0))
                ]])
                
                # Get prediction and probabilities
                prediction = model.predict(features)[0]
                probabilities = model.predict_proba(features)[0]
                
                # Display recommendation
                recommended_product = target_names[prediction]
                st.success(f"✨ Recommended Insurance Product: **{recommended_product}**")
                
                # Display input features
                st.write("\n#### Based on your profile:")
                st.write(f"• Savings Amount: ${investment_amount:,.2f}")
                st.write(f"• Monthly Card Spend: ${base_requirements['spend_amount']:,.2f}")
                st.write(f"• Has Existing Insurance: {'Yes' if base_requirements.get('has_insurance', 0) else 'No'}")
                
        else:
            st.error("Unable to load insurance recommendation model")
            
    except Exception as e:
        st.error("Error generating insurance recommendation")

if __name__ == "__main__":

    streamlit_app()