import streamlit as st
import pandas as pd
from Calculator import process_interest_rates

def interest_rates_page():
    st.title("🏦 Bank Interest Rates")
    
    # Add disclaimer
    st.markdown("""
        <div style='background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
            <span style='color: #c62828; font-weight: bold;'>⚠️ Disclaimer:</span>
            <span style='color: #c62828;'>
                Rates shown are for reference only. Please verify current rates with the respective banks.
            </span>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("Current interest rates and requirements for supported banks. Updated as of 16 Jan 2025.")
    
    # Load bank data
    banks_data = process_interest_rates()
    
    # Convert banks_data dictionary to a list of records
    records = []
    for bank_name, bank_info in banks_data.items():
        for tier in bank_info['tiers']:
            tier['bank'] = bank_name  # Add bank name to each tier
            records.append(tier)
    
    # Convert to DataFrame
    interest_rates_df = pd.DataFrame(records)
    
    # Add bank selector
    selected_bank = st.selectbox(
        "Select Bank",
        options=interest_rates_df['bank'].unique(),
        help="Choose a bank to view its interest rates"
    )
    
    # Show selected bank's data
    bank_data = interest_rates_df[interest_rates_df['bank'] == selected_bank]
    
    # Create a formatted table
    cols = ['tier_type', 'balance_tier', 'interest_rate', 'requirement_type', 'remarks']
    display_df = bank_data[cols].copy()
    display_df.columns = ['Tier Type', 'Balance Tier', 'Interest Rate (%)', 'Requirement', 'Remarks']
    
    # Display the table with styling
    st.dataframe(
        display_df,
        hide_index=True,
        column_config={
            "Interest Rate (%)": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
        },
        use_container_width=True
    )
    
    # Add explanatory notes
    with st.expander("Understanding Interest Tiers"):
        st.write("""
        ### Interest Rate Types
        - **Base Interest**: Basic interest rate applied to your deposit
        - **Bonus Interest**: Additional interest earned by meeting requirements
        
        ### Common Requirements
        - Salary crediting via GIRO
        - Monthly credit card spend
        - Bill payments
        - Investment or insurance products
        
        ### Important Notes
        - Interest rates are tiered based on deposit amount
        - Different requirements may apply for different tiers
        - Some banks cap the maximum eligible deposit amount
        """)

if __name__ == "__main__":
    interest_rates_page() 