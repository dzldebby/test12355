import pandas as pd
import numpy as np

def process_interest_rates(file_path):
    """Process the CSV file containing interest rate information."""
    try:
        # Read CSV file with correct encoding
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Convert interest_rate from percentage string to decimal
        df['interest_rate'] = df['interest_rate'].str.rstrip('%').astype('float') / 100.0
        print("\nDEBUG - Interest rates after conversion:")
        print(df[['bank', 'tier_type', 'interest_rate']].head())
        
        # Convert numeric columns
        numeric_columns = [
            'balance_tier',
            'min_spend',
            'min_salary',
            'giro_count',
            'cap_amount'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Convert Y/N to boolean
        df['salary_credit'] = df['salary_credit'].map({'Y': True, 'N': False})
        
        # Process data into a structured format
        banks_data = {}
        for bank in df['bank'].unique():
            bank_df = df[df['bank'] == bank]
            banks_data[bank] = bank_df.to_dict('records')
            print(f"\nDEBUG - {bank} data:")
            print(banks_data[bank])
        
        return banks_data
    except Exception as e:
        print(f"DEBUG - Error: {str(e)}")
        raise Exception(f"Error processing interest rates file: {str(e)}")

def calculate_bank_interest(deposit_amount, bank_info, requirements):
    """Calculate interest for a specific bank based on deposit amount and requirements."""
    try:
        print(f"\nDEBUG - Calculating for deposit: ${deposit_amount:,.2f}")
        print(f"DEBUG - Requirements: {requirements}")
        
        total_interest = 0
        breakdown = []
        
        # Group tiers by requirement_type
        requirement_groups = {}
        for tier in bank_info:
            req_type = tier['requirement_type']
            if req_type not in requirement_groups:
                requirement_groups[req_type] = []
            requirement_groups[req_type].append(tier)
        
        # Process each requirement type
        for req_type, tiers in requirement_groups.items():
            # Sort tiers by balance_tier
            sorted_tiers = sorted(tiers, key=lambda x: x['balance_tier'])
            amount_left = deposit_amount
            prev_cap = 0
            
            for tier in sorted_tiers:
                if amount_left <= 0:
                    break
                
                # Calculate amount for this tier
                tier_cap = tier['cap_amount']
                amount_in_tier = min(amount_left, tier_cap - prev_cap)
                
                if amount_in_tier <= 0:
                    continue
                
                print(f"\nDEBUG - Processing {req_type} tier: {tier['tier_type']}")
                print(f"DEBUG - Amount in tier: ${amount_in_tier:,.2f}")
                
                # Calculate interest rate based on requirements
                interest_rate = 0
                
                # Base interest
                if req_type == 'base':
                    interest_rate = tier['interest_rate']
                    print(f"DEBUG - Base rate: {interest_rate:.4%}")
                
                # Salary credit bonus
                elif req_type == 'salary' and requirements.get('has_salary', False):
                    if requirements.get('salary_amount', 0) >= tier.get('min_salary', 0):
                        interest_rate = tier['interest_rate']
                        print(f"DEBUG - Salary bonus rate: {interest_rate:.4%}")
                
                # Credit card spend bonus
                elif req_type == 'spend' and requirements.get('spend_amount', 0) >= tier.get('min_spend', 0):
                    interest_rate = tier['interest_rate']
                    print(f"DEBUG - Spend bonus rate: {interest_rate:.4%}")
                
                # Calculate interest for this tier
                tier_interest = amount_in_tier * interest_rate
                print(f"DEBUG - Tier interest: ${tier_interest:,.2f}")
                
                if tier_interest > 0:
                    breakdown.append({
                        'tier_type': tier['tier_type'],
                        'amount': amount_in_tier,
                        'rate': interest_rate,
                        'interest': tier_interest
                    })
                
                total_interest += tier_interest
                amount_left -= amount_in_tier
                prev_cap = tier_cap
        
        print(f"\nDEBUG - Total interest: ${total_interest:,.2f}")
        return {
            'total_interest': total_interest,
            'breakdown': breakdown
        }
        
    except Exception as e:
        print(f"DEBUG - Error: {str(e)}")
        raise Exception(f"Error calculating interest: {str(e)}")

def optimize_bank_distribution(total_amount, banks_data, user_requirements):
    """Find optimal distribution of funds across banks."""
    try:
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
        
        def try_combination(amounts_dict, salary_bank):
            # Calculate total interest for this distribution
            total_interest = 0
            breakdown = {}
            
            for bank, amount in amounts_dict.items():
                if amount > 0:
                    # Adjust requirements based on salary bank
                    bank_reqs = user_requirements.copy()
                    if bank == salary_bank:
                        bank_reqs['has_salary'] = True
                    elif bank == 'UOB One':
                        bank_reqs['has_salary'] = False
                    else:
                        bank_reqs['has_salary'] = False
                    
                    result = calculate_bank_interest(amount, banks_data[bank], bank_reqs)
                    total_interest += result['total_interest']
                    breakdown[bank] = result['breakdown']
            
            # Update top solutions if this is better
            for i, solution in enumerate(top_solutions):
                if total_interest > solution['total_interest']:
                    top_solutions[i] = {
                        'distribution': amounts_dict.copy(),
                        'total_interest': total_interest,
                        'breakdown': breakdown.copy(),
                        'salary_bank': salary_bank
                    }
                    break
        
        def try_all_combinations(remaining_amount, remaining_banks, current_distribution, salary_bank):
            if not remaining_banks:
                if abs(remaining_amount) < 5000:  # Allow small remainder
                    try_combination(current_distribution, salary_bank)
                return
            
            current_bank = remaining_banks[0]
            next_banks = remaining_banks[1:]
            
            # Try different amounts in $5000 increments
            max_amount = min(remaining_amount, bonus_caps[current_bank])
            for amount in range(0, max_amount + 5000, 5000):
                if amount <= remaining_amount:
                    new_distribution = current_distribution.copy()
                    if amount > 0:
                        new_distribution[current_bank] = amount
                    try_all_combinations(remaining_amount - amount, next_banks, new_distribution, salary_bank)
        
        # First try with salary credit
        if user_requirements.get('has_salary', False):
            for salary_bank in ['SC BonusSaver', 'OCBC 360', 'BOC SmartSaver']:
                non_salary_banks = [bank for bank in banks_data.keys() if bank != salary_bank]
                # Try salary bank first
                for amount in range(0, min(total_amount + 5000, bonus_caps[salary_bank] + 5000), 5000):
                    if amount <= total_amount:
                        initial_distribution = {salary_bank: amount} if amount > 0 else {}
                        try_all_combinations(total_amount - amount, non_salary_banks, initial_distribution, salary_bank)
        
        # Then try without salary credit
        try_all_combinations(total_amount, list(banks_data.keys()), {}, None)
        
        return top_solutions
        
    except Exception as e:
        raise Exception(f"Error optimizing distribution: {str(e)}")