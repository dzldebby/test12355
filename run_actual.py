import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

def calculate_bank_interest(deposit_amount, bank_info, bank_requirements):
    """Calculate interest based on the bank's tier structure and requirements"""
    total_interest = 0
    breakdown = []
    
    def add_tier(amount, rate, description=""):
        interest = amount * rate
        breakdown.append({
            'amount_in_tier': amount,
            'tier_rate': rate,
            'tier_interest': interest,
            'monthly_interest': interest / 12,
            'description': description
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
            if bank_requirements['has_salary']:
                # Spend + Salary (bonus interest)
                tiers = [t for t in bank_info['tiers'] if t['tier_type'] == 'spend_salary']
                for tier in tiers:
                    amount_in_tier = min(float(tier['cap_amount']), remaining_amount)
                    rate = float(str(tier['interest_rate']).strip('%')) / 100
                    bonus_rate = rate - base_rate  # Subtract base rate to get bonus
                    interest = amount_in_tier * bonus_rate
                    total_interest += interest
                    add_tier(amount_in_tier, bonus_rate, 
                        f"Bonus: Spend (${bank_requirements['spend_amount']:,.2f}) + Salary tier {tier['balance_tier']}")
                    remaining_amount -= amount_in_tier
                    if remaining_amount <= 0:
                        break
            elif bank_requirements['giro_count'] >= 3:
                # Spend + GIRO (bonus interest)
                tiers = [t for t in bank_info['tiers'] if t['tier_type'] == 'spend_giro']
                for tier in tiers:
                    amount_in_tier = min(float(tier['cap_amount']), remaining_amount)
                    rate = float(str(tier['interest_rate']).strip('%')) / 100
                    bonus_rate = rate - base_rate  # Subtract base rate to get bonus
                    interest = amount_in_tier * bonus_rate
                    total_interest += interest
                    add_tier(amount_in_tier, bonus_rate, 
                        f"Bonus: Spend (${bank_requirements['spend_amount']:,.2f}) + GIRO tier {tier['balance_tier']}")
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
                        f"Bonus: Spend only (${bank_requirements['spend_amount']:,.2f}) tier {tier['balance_tier']}")
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
            total_interest += add_tier(eligible_amount_100k, rate, 
                f"Card Spend Bonus (${bank_requirements['spend_amount']:,.2f})")
        
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
        add_tier(deposit_amount, base_rate, "Base Interest")
        
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
    print("\nOptimization Debug:")
    print(f"Total amount: ${total_amount:,.2f}")
    print(f"User requirements: {user_requirements}")
    
    # Initialize variables for best solution
    best_distribution = {}
    best_total_interest = 0
    best_breakdown = {}
    best_salary_bank = None
    
    # First, calculate interest for single-bank scenarios
    banks_to_try = ['UOB One', 'SC BonusSaver', 'OCBC 360', 'BOC SmartSaver', 'Chocolate']
    
    if user_requirements['has_salary']:
        # Try each bank as salary bank
        for salary_bank in ['UOB One', 'SC BonusSaver', 'OCBC 360', 'BOC SmartSaver']:
            # Create bank-specific requirements
            bank_reqs = user_requirements.copy()
            bank_reqs['has_salary'] = True
            
            # Calculate interest
            result = calculate_bank_interest(total_amount, banks_data[salary_bank], bank_reqs)
            if result['total_interest'] > best_total_interest:
                best_total_interest = result['total_interest']
                best_distribution = {salary_bank: total_amount}
                best_breakdown = {salary_bank: result['breakdown']}
                best_salary_bank = salary_bank
                print(f"New best found: {salary_bank} with ${best_total_interest:,.2f}")
    
    # Also try without salary credit for all banks
    for bank in banks_to_try:
        bank_reqs = user_requirements.copy()
        bank_reqs['has_salary'] = False
        
        result = calculate_bank_interest(total_amount, banks_data[bank], bank_reqs)
        if result['total_interest'] > best_total_interest:
            best_total_interest = result['total_interest']
            best_distribution = {bank: total_amount}
            best_breakdown = {bank: result['breakdown']}
            best_salary_bank = None
            print(f"New best found: {bank} with ${best_total_interest:,.2f}")
    
    return {
        'distribution': best_distribution,
        'total_interest': best_total_interest,
        'breakdown': best_breakdown,
        'salary_bank': best_salary_bank
    }

def streamlit_app():
    st.title("Bank Interest Rate Optimizer")
    
    try:
        # Load and process the CSV file
        banks_data = process_interest_rates('interest_rates.csv')
        
        # User inputs for amount
        investment_amount = st.number_input(
            "Investment Amount ($)", 
            min_value=0.0, 
            value=10000.0, 
            step=1000.0,
            key="investment_amount_main"
        )
        
        # Collect all requirements in one section
        st.subheader("Your Banking Activities - updated 05/01/2025")
        
        # Credit Card Spending
        with st.expander("Credit Card Spending", expanded=True):
            card_spend = st.number_input(
                "Monthly Card Spend ($)", 
                min_value=0.0, 
                step=100.0,
                key="card_spend_input"
            )
        
        # Salary Credit
        with st.expander("Salary Credit", expanded=True):
            has_salary = st.checkbox(
                "Credit Salary via GIRO/PayNow/FAST", 
                key="salary_credit_checkbox"
            )
            salary_amount = st.number_input(
                "Monthly Salary Amount ($)", 
                min_value=0.0, 
                step=100.0,
                key="salary_amount_input"
            ) if has_salary else 0
        
        # Bill Payments
        with st.expander("Bill Payments", expanded=True):
            giro_count = st.number_input(
                "Number of Bill Payments (GIRO/Online Banking)", 
                min_value=0, 
                step=1,
                key="bill_payments_input"
            )
            st.caption("Note: For BOC SmartSaver, payments can be made via GIRO or Internet/Mobile Banking (min. $30 each)")
            st.caption("For UOB One, only GIRO transactions are counted")
        
        # Insurance
        with st.expander("Insurance Products", expanded=True):
            has_insurance = st.checkbox(
                "Purchased Eligible Insurance Products",
                key="insurance_checkbox"
            )
        
        # Investments
        with st.expander("Investments", expanded=True):
            has_investments = st.checkbox(
                "Made Eligible Investments",
                key="investments_checkbox"
            )
        
        # Account Balance Growth
        with st.expander("Account Balance Growth", expanded=True):
            has_increased_balance = st.checkbox(
                "Increased Account Balance Month-on-Month",
                key="balance_increase_checkbox"
            )
            has_grow = st.checkbox(
                "Increased Wealth Balance (OCBC)",
                key="wealth_growth_checkbox"
            )
        
        # Create requirements dictionary
        base_requirements = {
            'spend_amount': card_spend,
            'has_salary': has_salary,
            'salary_amount': salary_amount,
            'giro_count': giro_count,
            'has_insurance': has_insurance,
            'has_investments': has_investments,
            'has_increased_balance': has_increased_balance,
            'has_grow': has_grow
        }
        
        # Calculate for all banks
        st.subheader("Interest Rates Comparison")
        
        # Calculate and display results for each bank
        bank_results = []
        for bank_name in ["UOB One", "SC BonusSaver", "OCBC 360", "BOC SmartSaver", "Chocolate"]:
            results = calculate_bank_interest(investment_amount, banks_data[bank_name], base_requirements)
            bank_results.append({
                'bank': bank_name,
                'monthly_interest': results['total_interest']/12,
                'annual_interest': results['total_interest'],
                'breakdown': results['breakdown']
            })
        
        # Sort banks by monthly interest (highest first)
        bank_results.sort(key=lambda x: x['monthly_interest'], reverse=True)
        
        # Display comparison table
        comparison_data = {
            'Bank': [r['bank'] for r in bank_results],
            'Monthly Interest': [f"${r['monthly_interest']:,.2f}" for r in bank_results],
            'Annual Interest': [f"${r['annual_interest']:,.2f}" for r in bank_results],
            'Effective Rate': [
                f"{(r['annual_interest'] / (50000 if r['bank'] == 'Chocolate' else investment_amount) * 100):,.2f}%" 
                for r in bank_results
            ]
        }
        st.table(comparison_data)
        
        # Display detailed breakdown for each bank
        for result in bank_results:
            with st.expander(f"Details for {result['bank']}", expanded=False):
                st.write(f"### {result['bank']}")
                st.write(f"Monthly Interest: ${result['monthly_interest']:,.2f}")
                st.write(f"Annual Interest: ${result['annual_interest']:,.2f}")
                st.write("#### Interest Breakdown")
                for tier in result['breakdown']:
                    st.write(f"Amount in Tier: ${tier['amount_in_tier']:,.2f}")
                    st.write(f"Interest Rate: {tier['tier_rate']*100:.2f}%")
                    st.write(f"Annual Interest: ${tier['tier_interest']:,.2f}")
                    st.write(f"Monthly Interest: ${tier['monthly_interest']:,.2f}")
                    st.write(f"Description: {tier['description']}")
                    st.write("---")
        
        # Add Optimization Section
        st.subheader("Optimal Distribution")
        if st.button("Calculate Optimal Distribution"):
            optimization_result = optimize_bank_distribution(
                investment_amount,
                banks_data,
                base_requirements
            )
            
            # Display optimal distribution
            st.write("### Recommended Distribution")
            st.write(f"Best Annual Interest: ${optimization_result['total_interest']:,.2f}")
            st.write(f"Best Monthly Interest: ${optimization_result['total_interest']/12:,.2f}")
            
            # Show salary credit recommendation if applicable
            if base_requirements['has_salary'] and optimization_result['salary_bank']:
                st.write("---")
                st.write(f"🔵 Credit your salary to: **{optimization_result['salary_bank']}**")
            
            st.write("---")
            # Show the distribution
            for bank, amount in optimization_result['distribution'].items():
                if amount > 0:
                    if bank == optimization_result['salary_bank']:
                        st.write(f"💰 {bank} (Salary Credit): ${amount:,.2f}")
                    else:
                        st.write(f"💰 {bank}: ${amount:,.2f}")
            
            # Show detailed breakdown
            with st.expander("See Detailed Breakdown"):
                for bank, breakdown in optimization_result['breakdown'].items():
                    if bank in optimization_result['distribution'] and optimization_result['distribution'][bank] > 0:
                        if bank == optimization_result['salary_bank']:
                            st.write(f"#### {bank} (Salary Credit Bank)")
                        else:
                            st.write(f"#### {bank}")
                        for tier in breakdown:
                            st.write(f"- Amount: ${tier['amount_in_tier']:,.2f}")
                            st.write(f"  Rate: {tier['tier_rate']*100:.2f}%")
                            st.write(f"  Interest: ${tier['tier_interest']:,.2f}")
                            st.write(f"  Description: {tier['description']}")
                        st.write("---")
                    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

if __name__ == "__main__":
    streamlit_app()