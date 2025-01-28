import streamlit as st

def methodology_page():
    st.title("📊 Calculation Methodology")
    
    st.write("""
    This calculator uses a systematic approach to determine optimal bank interest rates 
    and deposit allocation strategies.
    """)
    
    # Overview
    st.header("Overview")
    st.write("""
    Our calculations consider multiple factors including:
    - Base interest rates
    - Bonus interest tiers
    - Salary crediting requirements
    - Credit card spend requirements
    - Bill payment conditions
    """)
    
    # Detailed Methodology
    st.header("Detailed Methodology")
    
    with st.expander("1. Base Rate Calculation"):
        st.write("""
        Base interest rates are calculated using:
        - Published bank rates
        - Deposit amount tiers
        - Account type specifications
        """)
    
    with st.expander("2. Bonus Interest Qualification"):
        st.write("""
        Bonus interest is determined by:
        1. Salary crediting status
        2. Monthly credit card spend
        3. Number of bill payments
        4. Investment/Insurance products
        5. Account balance growth
        """)
        
        st.info("""
        💡 Example: For UOB One, meeting salary crediting OR card spend requirements 
        can qualify for bonus interest tiers.
        """)
    
    with st.expander("3. Optimization Algorithm"):
        st.write("""
        The optimization process:
        1. Evaluates all possible combinations of deposit allocation
        2. Considers minimum requirements for each bank
        3. Maximizes total interest earned
        4. Accounts for practical constraints
        """)
        
        st.code("""
        def optimize_allocation(deposit, requirements):
            best_allocation = None
            max_interest = 0
            
            for allocation in generate_valid_allocations(deposit):
                interest = calculate_total_interest(allocation)
                if interest > max_interest:
                    max_interest = interest
                    best_allocation = allocation
                    
            return best_allocation
        """, language="python")
    
    # Data Sources
    st.header("Data Sources")
    st.write("""
    Interest rates and requirements are sourced from:
    - Official bank websites
    - MAS published data
    - Bank product sheets
    
    Last updated: February 2024
    """)
    
    # Limitations
    st.header("Limitations")
    st.warning("""
    ⚠️ Please note:
    - Rates may change without notice
    - Some bank promotions may not be included
    - Individual eligibility criteria may vary
    - Special rates for priority banking are not included
    """)
    

if __name__ == "__main__":
    methodology_page() 