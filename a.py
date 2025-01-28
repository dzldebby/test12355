import pandas as pd


def create_complete_bank_tiers():
    banks_data = {
        'BOC SmartSaver': {
            'base_interest': 0.0080,
            'tiers': [
                {'type': 'wealth', 'rate': 0.0240, 'requirement': 'Insurance purchase'},
                {'type': 'card_spend_1', 'rate': 0.0050, 'min_spend': 500},
                {'type': 'card_spend_2', 'rate': 0.0080, 'min_spend': 1500},
                {'type': 'salary_1', 'rate': 0.0190, 'min_salary': 2000},
                {'type': 'salary_2', 'rate': 0.0250, 'min_salary': 6000},
                {'type': 'payment', 'rate': 0.0090, 'requirement': '3 bill payments ≥$30'},
                {'type': 'extra', 'rate': 0.0060, 'requirement': 'Any qualifying category'}
            ],
            'max_interest': 0.0700,
            'cap_amount': 75000
        },
        'Citi Interest Booster': {
            'base_interest': 0.0150,
            'tiers': [
                {'type': 'save', 'rate': 0.0020, 'requirement': 'Increase balance by $1,500'},
                {'type': 'spend', 'rate': 0.0020, 'min_spend': 500},
                {'type': 'invest', 'rate': 0.0060, 'requirement': '3 investments ≥$1,000'},
                {'type': 'insure', 'rate': 0.0060, 'requirement': 'Policy ≥$5,000 premium'},
                {'type': 'mortgage', 'rate': 0.0080, 'requirement': 'Home loan ≥$500,000'},
                {'type': 'birthday', 'rate': 0.0010, 'requirement': 'Birthday month'}
            ],
            'max_interest': 0.0400,
            'cap_amount': 50000
        },
        'DBS Multiplier': {
            'base_interest': 0.0050,
            'tiers': [
                # Income + 1 category
                {'type': 'tier1_1cat', 'rate': 0.0180, 'total_txn': 500, 'cap': 50000},
                {'type': 'tier2_1cat', 'rate': 0.0190, 'total_txn': 15000, 'cap': 50000},
                {'type': 'tier3_1cat', 'rate': 0.0220, 'total_txn': 30000, 'cap': 50000},
                # Income + 2 categories
                {'type': 'tier1_2cat', 'rate': 0.0210, 'total_txn': 500, 'cap': 100000},
                {'type': 'tier2_2cat', 'rate': 0.0220, 'total_txn': 15000, 'cap': 100000},
                {'type': 'tier3_2cat', 'rate': 0.0300, 'total_txn': 30000, 'cap': 100000},
                # Income + 3 categories
                {'type': 'tier1_3cat', 'rate': 0.0240, 'total_txn': 500, 'cap': 100000},
                {'type': 'tier2_3cat', 'rate': 0.0250, 'total_txn': 15000, 'cap': 100000},
                {'type': 'tier3_3cat', 'rate': 0.0410, 'total_txn': 30000, 'cap': 100000}
            ],
            'max_interest': 0.0410,
            'cap_amount': 100000
        },
        'HSBC EGA': {
            'base_interest': 0.0005,
            'tiers': [
                {'type': 'bonus_tier1', 'rate': 0.0325, 'balance': 2000000},
                {'type': 'bonus_tier2', 'rate': 0.0335, 'balance': 'Above 2000000'},
                {'type': 'everyday_plus', 'rate': 0.0100, 'requirement': 'Everyday+ Rewards'},
                {'type': 'additional', 'rate': 0.0100, 'requirement': 'Additional bonus'}
            ],
            'max_interest': 0.0440,
            'cap_amount': 2000000
        },
        'Maybank Save Up': {
            'base_interest': 0.0025,
            'tiers': [
                # First $50,000
                {'type': 'tier1_1prod', 'rate': 0.0030, 'products': 1, 'cap': 50000},
                {'type': 'tier1_2prod', 'rate': 0.0100, 'products': 2, 'cap': 50000},
                {'type': 'tier1_3prod', 'rate': 0.0275, 'products': 3, 'cap': 50000},
                # Next $25,000
                {'type': 'tier2_1prod', 'rate': 0.0100, 'products': 1, 'cap': 25000},
                {'type': 'tier2_2prod', 'rate': 0.0150, 'products': 2, 'cap': 25000},
                {'type': 'tier2_3prod', 'rate': 0.0375, 'products': 3, 'cap': 25000}
            ],
            'max_interest': 0.0400,
            'cap_amount': 75000
        },
        'OCBC 360': {
            'base_interest': 0.0005,
            'tiers': [
                # First $75,000
                {'type': 'salary', 'rate': 0.0200, 'requirement': 'Min $1,800 salary'},
                {'type': 'save', 'rate': 0.0120, 'requirement': 'Increase $500 monthly'},
                {'type': 'spend', 'rate': 0.0060, 'requirement': 'Min $500 spend'},
                {'type': 'invest', 'rate': 0.0120, 'requirement': 'Eligible investment'},
                {'type': 'insure', 'rate': 0.0120, 'requirement': 'Eligible insurance'},
                # Next $25,000
                {'type': 'wealth', 'rate': 0.0400, 'requirement': 'Min $200,000 balance'}
            ],
            'max_interest': 0.0765,
            'cap_amount': 100000
        },
        'SCB BonusSaver': {
            'base_interest': 0.0005,
            'tiers': [
                {'type': 'spend_1', 'rate': 0.0060, 'min_spend': 500},
                {'type': 'spend_2', 'rate': 0.0140, 'min_spend': 2000},
                {'type': 'salary', 'rate': 0.0200, 'min_salary': 3000},
                {'type': 'bill', 'rate': 0.0023, 'requirement': '3 bills ≥$50'},
                {'type': 'invest', 'rate': 0.0200, 'requirement': 'Unit trust ≥$30,000'},
                {'type': 'insure', 'rate': 0.0200, 'requirement': 'Insurance ≥$12,000'}
            ],
            'max_interest': 0.0768,
            'cap_amount': 100000
        },
        'UOB One': {
            'base_interest': 0.0005,
            'tiers': [
                # Card spend only
                {'type': 'spend', 'rate': 0.0065, 'min_spend': 500, 'cap': 75000},
                # Card spend + GIRO
                {'type': 'spend_giro_1', 'rate': 0.0200, 'min_spend': 500, 'cap': 75000},
                {'type': 'spend_giro_2', 'rate': 0.0300, 'min_spend': 500, 'cap': 50000},
                # Card spend + Salary
                {'type': 'spend_salary_1', 'rate': 0.0300, 'min_spend': 500, 'cap': 75000},
                {'type': 'spend_salary_2', 'rate': 0.0450, 'min_spend': 500, 'cap': 50000},
                {'type': 'spend_salary_3', 'rate': 0.0600, 'min_spend': 500, 'cap': 25000}
            ],
            'max_interest': 0.0600,
            'cap_amount': 150000
        }
    }
    return banks_data


    import pandas as pd

def convert_to_csv(banks_data):
    rows = []
    
    for bank_name, bank_info in banks_data.items():
        # Process each tier
        for tier in bank_info['tiers']:
            row = {
                'bank': bank_name,
                'base_interest': f"{bank_info['base_interest']*100:.2f}%",
                'tier_type': tier['type'],
                'bonus_rate': f"{tier['rate']*100:.2f}%",
                'requirement': ''
            }
            
            # Add requirements based on tier type
            if 'requirement' in tier:
                row['requirement'] = tier['requirement']
            elif 'min_spend' in tier:
                row['requirement'] = f"Min spend ${tier['min_spend']:,}"
            elif 'min_salary' in tier:
                row['requirement'] = f"Min salary ${tier['min_salary']:,}"
            elif 'total_txn' in tier:
                row['requirement'] = f"Total transactions ${tier['total_txn']:,}"
            elif 'balance' in tier:
                row['requirement'] = f"Balance ${tier['balance']:,}" if isinstance(tier['balance'], (int, float)) else tier['balance']
            elif 'products' in tier:
                row['requirement'] = f"{tier['products']} product(s)"
            
            # Add cap amount if present
            row['cap_amount'] = tier.get('cap', bank_info['cap_amount'])
            
            # Add maximum possible interest
            row['max_interest'] = f"{bank_info['max_interest']*100:.2f}%"
            
            rows.append(row)
    
    # Convert to DataFrame and save as CSV
    df = pd.DataFrame(rows)
    
    # Reorder columns
    columns = ['bank', 'base_interest', 'tier_type', 'bonus_rate', 'requirement', 
              'cap_amount', 'max_interest']
    df = df[columns]
    
    # Save to CSV
    df.to_csv('bank_interest_rates.csv', index=False)
    return df

def main():
    banks_data = create_complete_bank_tiers()
    df = convert_to_csv(banks_data)
    print("CSV file created successfully!")
    return df

if __name__ == "__main__":
    main()