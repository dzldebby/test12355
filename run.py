import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog
import traceback
from analytics import (
    identify_user, 
    assign_variant, 
    track_calculation, 
    track_bank_interaction,
    track_error
)

def calculate_bank_interest(deposit_amount, bank_info, bank_requirements):
    """Calculate interest based on the bank's tier structure and requirements"""
    total_interest = 0
    breakdown = []
    
    # In the add_tier function
    def add_tier(amount, rate, description=""):
        interest = amount * rate
        # Debug print
        print(f"Adding tier: amount={amount}, rate={rate}, description={description}")
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
        # First add base interest for entire amount
        base_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'base')
        base_rate = float(str(base_tier['interest_rate']).strip('%')) / 100
        total_interest += add_tier(deposit_amount, base_rate, "Base interest rate")
        
        # Then add bonus interest based on requirements
        if bank_requirements['spend_amount'] >= 500:
            remaining_amount = deposit_amount
            if bank_requirements['meets_criteria_a']:
                # Criteria A + Spend
                tiers = [t for t in bank_info['tiers'] if t['tier_type'] == 'criteria_a']
                for tier in tiers:
                    amount_in_tier = min(float(tier['cap_amount']), remaining_amount)
                    rate = float(str(tier['interest_rate']).strip('%')) / 100
                    bonus_rate = rate - base_rate  # Subtract base rate to get bonus
                    interest = amount_in_tier * bonus_rate
                    total_interest += interest
                    add_tier(amount_in_tier, bonus_rate, 
                        f"Salary Credit  + Credit Card Spend (${bank_requirements['spend_amount']:,.2f}) for {tier['balance_tier']}")
                    remaining_amount -= amount_in_tier
                    if remaining_amount <= 0:
                        break
            else:
                # Spend only (bonus interest)
                tiers = [t for t in bank_info['tiers'] if t['tier_type'] == 'spend_only']
                for tier in tiers:
                    amount_in_tier = min(float(tier['cap_amount']), remaining_amount)
                    rate = float(str(tier['interest_rate']).strip('%')) / 100
                    bonus_rate = rate - base_rate  # Subtract base rate to get bonus
                    interest = amount_in_tier * bonus_rate
                    total_interest += interest
                    add_tier(amount_in_tier, bonus_rate, 
                        f"Credit card spend (${bank_requirements['spend_amount']:,.2f}) interest")
                    remaining_amount -= amount_in_tier
                    if remaining_amount <= 0:
                        break
    
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
        process_ocbc_tier('save', bank_requirements.get('has_increased_balance', False))
        
        # Spend bonus
        spend_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'spend')
        has_spend = bank_requirements['spend_amount'] >= float(spend_tier['min_spend'])
        process_ocbc_tier('spend', has_spend)
        
        # Insurance bonus
        process_ocbc_tier('insure', bank_requirements.get('has_insurance', False))
        
        # Investment bonus
        process_ocbc_tier('invest', bank_requirements.get('has_investments', False))
        
        # Grow bonus
        process_ocbc_tier('grow', bank_requirements.get('has_grow', False))
        
        total_interest += total_first_75k + total_next_25k
    
    elif bank_info['bank'] == 'BOC SmartSaver':
        # Always add base interest first for total amount
        base_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'base')
        base_rate = float(str(base_tier['interest_rate']).strip('%')) / 100
        total_interest = deposit_amount * base_rate
        add_tier(deposit_amount, base_rate, "Base Interest")
        
        # Calculate bonus interest for first $100k
        eligible_amount_100k = min(deposit_amount, 100000)
        
        # Wealth bonus (Insurance)
        if bank_requirements['has_insurance']:
            wealth_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'wealth')
            rate = float(str(wealth_tier['interest_rate']).strip('%')) / 100
            total_interest += add_tier(eligible_amount_100k, rate, "Insurance Purchase Bonus")
        
        # Card spend bonus
        if bank_requirements['spend_amount'] >= 500:
            spend_tiers = [t for t in bank_info['tiers'] if t['tier_type'] == 'spend']
            spend_tier = spend_tiers[1] if bank_requirements['spend_amount'] >= 1500 else spend_tiers[0]
            rate = float(str(spend_tier['interest_rate']).strip('%')) / 100
            
            # Debug print
            print(f"Spend tier description: {spend_tier['remarks']}")
            print(f"Formatted description: Card Spend Bonus (${bank_requirements['spend_amount']:,.2f})")
            
            description = f"Card Spend Bonus (${bank_requirements['spend_amount']:,.2f})"
            total_interest += add_tier(eligible_amount_100k, rate, description)
        
        # Salary bonus
        if bank_requirements['has_salary'] and bank_requirements['salary_amount'] >= 2000:
            salary_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'salary')
            rate = float(str(salary_tier['interest_rate']).strip('%')) / 100
            total_interest += add_tier(eligible_amount_100k, rate, "Salary Credit Bonus")
        
        # Payment bonus
        if bank_requirements['giro_count'] >= 3:
            payment_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'payment')
            rate = float(str(payment_tier['interest_rate']).strip('%')) / 100
            total_interest += add_tier(eligible_amount_100k, rate, "Bill Payment Bonus")
        
        # Extra savings bonus (applies to balance above $100k up to $1M)
        # Only if any of card spend, salary, or payment bonus is met
        has_qualifying_bonus = (
            (bank_requirements['spend_amount'] >= 500) or
            (bank_requirements['has_salary'] and bank_requirements['salary_amount'] >= 2000) or
            (bank_requirements['giro_count'] >= 3)
        )
        
        if has_qualifying_bonus and deposit_amount > 100000:
            extra_tier = next(t for t in bank_info['tiers'] if t['tier_type'] == 'extra')
            rate = float(str(extra_tier['interest_rate']).strip('%')) / 100
            extra_amount = min(deposit_amount - 100000, 900000)  # Cap at $1M total
            total_interest += add_tier(extra_amount, rate, "Extra Savings Bonus (>$100k)")
    
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
        print(f"\nProcessing bank: {bank_name}")
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
                    print(f"Added tier: {tier}")
                    
                except (ValueError, TypeError) as e:
                    print(f"Error processing tier: {e}")
            
            print(f"Successfully added {len(banks_data[bank_name]['tiers'])} tiers for {bank_name}")
                
        except Exception as e:
            print(f"Error processing {bank_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nFinished processing. Found {len(banks_data)} banks")
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
                    bank_reqs['meets_criteria_a'] = user_requirements['meets_criteria_a']
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

def is_mobile():
    """Check if current view is from a mobile device"""
    try:
        # Get viewport width from streamlit
        viewport = st.get_option('client.displayWidth')
        return viewport < 768  # Standard mobile breakpoint
    except:
        return False

# Set page config (without mobile check initially)
st.set_page_config(
    page_title="SmartSaverSG",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def streamlit_app():
    try:
        # User identification
        user_id = identify_user()
        variant = assign_variant()
        # Add mobile detection and sidebar control
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            /* Hide fork button and GitHub link */
            .stActionButton, .viewerBadge_container__1QSob {
                display: none !important;
            }
            /* Hide 'deploy' button */
            .stDeployButton {
                display: none !important;
            }
            /* Remove padding/margin from the top of the page */
            .block-container {
                padding-top: 1rem !important;
            }
            /* Hide hamburger menu */
            .css-r698ls {
                display: none;
            }
            /* Hide 'Made with Streamlit' */
            .css-1vq4p4l {
                display: none;
            }
            </style>
            <script>
                function detectMob() {
                    const toMatch = [
                        /Android/i,
                        /webOS/i,
                        /iPhone/i,
                        /iPad/i,
                        /iPod/i,
                        /BlackBerry/i,
                        /Windows Phone/i
                    ];
                    
                    return toMatch.some((toMatchItem) => {
                        return navigator.userAgent.match(toMatchItem);
                    });
                }

                // If not mobile, expand sidebar
                if (!detectMob()) {
                    const sidebarExpander = document.querySelector('button[kind="secondary"][aria-label="Toggle sidebar visibility"]');
                    if (sidebarExpander) {
                        sidebarExpander.click();
                    }
                }
            </script>
        """, unsafe_allow_html=True)
        
        # Then: Load interest rates data
        banks_data = process_interest_rates()
        
        st.title("🏦 SmartSaverSG")
        st.subheader("Maximize Your Savings with Bank Interest Calculator")
        
        st.write("""
            SmartSaverSG helps you optimize your savings by analyzing multiple bank accounts 
            and their requirements to find the best interest rates. Simply enter your deposit 
            amount and banking preferences to get recommendations.
        """)


        # Requirements Section
        st.write("##### Step 1: Enter Your Banking Activities")
        
        try:
            # # Investment Amount Input
            # amount_str = st.text_input(
            #     "Total Amount of Savings ($)", 
            #     value="10,000",
            #     help="Enter amount with commas (e.g., 100,000)"
            # )
            # investment_amount = int(amount_str.replace(",", ""))


            # Add A/B test variations for the input interface
            if variant == 'A':
                # Variant A: Text input (original)
                amount_str = st.text_input(
                    "Total Amount of Savings ($)", 
                    value="10,000",
                    help="Enter amount with commas (e.g., 100,000)"
                )
                investment_amount = int(amount_str.replace(",", ""))
            else:
                # Variant B: Slider input
                amount_str = st.slider(
                    "Total Amount of Savings ($)",
                    min_value=0,
                    max_value=1000000,
                    value=10000,
                    step=1000,
                    format="$%d"
                )
                investment_amount = int(amount_str)

            
            
            # Organize requirements into logical groups using columns and expanders
            col1, col2 = st.columns(2)
            
            with col1:
                # Salary and Spending
                with st.expander("💳 Income & Spending", expanded=True):
                    has_salary = st.toggle(
                        "Credit salary via GIRO",
                        help="For SC BonusSaver, OCBC 360, BOC SmartSaver"
                    )
                    if has_salary:
                        salary_amount = st.number_input(
                            "Monthly Salary ($)",
                            min_value=0,
                            max_value=50000,
                            value=5000,
                            step=100,
                            format="%d"
                        )
                        st.caption(f"Selected Salary: ${format_number(salary_amount)}")
                    else:
                        salary_amount = 0
                    
                    card_spend = st.number_input(
                        "Monthly Card Spend ($)",
                        min_value=0,
                        max_value=10000,
                        value=500,
                        step=100,
                        format="%d"
                    )
                    st.caption(f"Selected Card Spend: ${format_number(card_spend)}")
            
            with col2:
                # Additional Requirementsg
                with st.expander("🏦 Additional Requirements", expanded=True):
                    meets_criteria_a = st.toggle(
                        "UOB One Salary Credit",
                        help="For UOB One, salary can be simulated"
                    )
                    
                    giro_count = st.number_input(
                        "Number of Bill Payments",
                        min_value=0,
                        step=1
                    )
            
            # Advanced Requirements
            with st.expander("📈 Bank-specific Bonuses", expanded=False):
                col3, col4 = st.columns(2)
                with col3:
                    has_insurance = st.toggle(
                        "Have Insurance Products",
                        help="""Select this if you have any of the following insurance:\n
                        • SC BonusSaver: Purchase eligible insurance products\n
                        • OCBC 360: Min. S$2,000 annual insurance premium\n
                        • BOC SmartSaver: Purchase eligible insurance products"""
                    )
                    has_investments = st.toggle(
                        "Have Investments",
                        help="""Select this if you have any of the following investments:\n
                        • SC BonusSaver: Invest in eligible investment products\n
                        • OCBC 360: Min. S$2,000 in eligible investment products"""
                    )
                with col4:
                    has_increased_balance = st.toggle("[OCBC] Increased Monthly Balance",
                                                    help="Increase your OCBC account average daily balance by at least S$500 monthly")
                    has_grow = st.toggle("[OCBC] Increased Wealth Balance",
                                        help="Maintain an average daily balance on OCBC account of at least S$200,000")
            
            # Create base requirements dictionary (moved outside tabs)
            base_requirements = {
                'has_salary': bool(has_salary and salary_amount >= 2000),
                'salary_amount': salary_amount,
                'spend_amount': card_spend,
                'meets_criteria_a': meets_criteria_a,
                'giro_count': giro_count,
                'has_insurance': has_insurance,
                'has_investments': has_investments,
                'has_increased_balance': has_increased_balance,
                'has_grow': has_grow
            }

            # Create a more descriptive section for the two options
            st.write("##### Step 2: Select your calculation method:")
            
            # Create tabs with clearer descriptions and icons
            tab1, tab2 = st.tabs([
                "🏦 Single Bank Calculator",
                "🔄 Multi-Bank Optimizer"
            ])
            
            with tab1:
                st.write("""
                    **Calculate interest for a single bank account**
                    - See detailed breakdowns for each bank
                    - Compare base rates and bonus interest
                    - Understand requirements for each bank
                """)
                
                if st.button("Calculate Single Bank Interest", type="primary", key="single_bank_calc"):
                    with st.spinner("Calculating interest rates..."):
                        # Calculate and display results for each bank
                        bank_results = []
                        for bank_name in ["UOB One", "SC BonusSaver", "OCBC 360", "BOC SmartSaver", "Chocolate"]:
                            bank_reqs = base_requirements.copy()
                            
                            # Special handling for UOB One
                            if bank_name == 'UOB One':
                                bank_reqs['meets_criteria_a'] = base_requirements.get('meets_criteria_a', False)
                                bank_reqs['has_salary'] = False  # UOB One uses meets_criteria_a instead
                            
                            results = calculate_bank_interest(investment_amount, banks_data[bank_name], bank_reqs)
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
                        st.write("### 🏆 Optimal Choice")
                        st.success(f"**{optimal_bank['bank']}** offers the highest interest rate!")
                        col_opt1, col_opt2 = st.columns(2)
                        with col_opt1:
                            st.metric("Monthly Interest", f"${optimal_bank['monthly_interest']:,.2f}")
                        with col_opt2:
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
                        
                        # Divider between optimal and all results
                        st.markdown("---")
                        
                        # Display All Bank Results
                        st.write("### All Bank Details")
                        for result in bank_results:
                            with st.expander(f"{result['bank']} Details", expanded=False):
                                # Create two columns for Monthly and Annual Interest
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Monthly Interest", f"${result['monthly_interest']:,.2f}")
                                with col2:
                                    st.metric("Annual Interest", f"${result['annual_interest']:,.2f}")
                                
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
            
            with tab2:
                st.write("""
                    **Optimize across multiple banks**
                    - Find the best combination of accounts
                    - Maximize your total interest earned
                    - Get recommendations for salary crediting and spending
                """)
                
                if st.button("Calculate Optimal Distribution", type="primary", key="multi_bank_calc"):
                    with st.spinner("Optimizing distribution..."):
                        # First optimize deposit distribution
                        top_solutions = optimize_bank_distribution(
                            investment_amount,
                            banks_data,
                            base_requirements
                        )
                        
                        # Then optimize spend allocation for each solution
                        for solution in top_solutions:
                            if solution['total_interest'] > 0:
                                spend_allocation, new_total_interest, interest_breakdown = optimize_spend_allocation(
                                    card_spend,
                                    banks_data,
                                    solution['distribution'],
                                    base_requirements
                                )
                                
                                # Update solution with spend allocation
                                solution['spend_allocation'] = spend_allocation
                                solution['total_interest'] = new_total_interest
                                solution['interest_breakdown'] = interest_breakdown
                        
                        # Display optimization results
                        for i, solution in enumerate(top_solutions):
                            if solution['total_interest'] > 0:
                                with st.expander(f"💡 Optimization Scenario {i+1}", expanded=(i==0)):
                                    col7, col8 = st.columns(2)
                                    with col7:
                                        st.metric(
                                            "Monthly Interest",
                                            f"${solution['total_interest']/12:,.2f}"
                                        )
                                    with col8:
                                        st.metric(
                                            "Annual Interest",
                                            f"${solution['total_interest']:,.2f}"
                                        )
                                        
                                        # Deposit Distribution
                                        st.write("### 💰 Recommended Deposit Distribution")
                                        for bank, amount in solution['distribution'].items():
                                            if amount > 0:
                                                st.write(f"• {bank}: ${amount:,.2f}")
                                        
                                        # Credit Card Spend Distribution
                                        if solution.get('spend_allocation'):
                                            st.write("\n### 💳 Credit Card Spend Distribution")
                                            total_allocated = sum(solution['spend_allocation'].values())
                                            remaining_spend = card_spend - total_allocated
                                            
                                            for bank, spend in solution['spend_allocation'].items():
                                                percentage = (spend / card_spend) * 100
                                                st.write(f"• {bank}: ${spend:,.2f} ({percentage:.1f}%)")
                                            
                                            if remaining_spend > 0:
                                                percentage = (remaining_spend / card_spend) * 100
                                                st.write(f"• Remaining unallocated spend: ${remaining_spend:,.2f} ({percentage:.1f}%)")
                                        
                                        # Salary Credit Info
                                        if base_requirements['has_salary'] and solution['salary_bank']:
                                            st.info(f"💡 Credit your salary to: {solution['salary_bank']}")



                        # Add disclaimer in red
            st.markdown("""
                <div style='background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
                    <span style='color: #c62828; font-weight: bold;'>⚠️ Disclaimer:</span>
                    <span style='color: #c62828;'>
                        This calculator provides general information only and does not constitute financial advice. 
                        Please verify all rates with the respective banks and consult a financial advisor for personalized recommendations.
                    </span>
                </div>
            """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.error(traceback.format_exc())

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
                    bank_reqs['meets_criteria_a'] = base_requirements.get('meets_criteria_a', False)
                    bank_reqs['has_salary'] = False  # UOB One uses meets_criteria_a instead
                
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

if __name__ == "__main__":
    streamlit_app()