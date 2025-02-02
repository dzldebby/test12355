import streamlit as st

def main():
    st.title("📚 How to Use the Calculator")
    
    st.header("Single Bank Calculator Tutorial")
    
    # Step 1
    st.subheader("Step 1: Enter Your Investment Amount")
    st.markdown("""
    - Enter the amount you plan to deposit in your savings account
    - You can either:
        - Type the amount directly
        - Use the + / - buttons to adjust
        - Use the slider to select an amount
    """)
    
    # Step 2
    st.subheader("Step 2: Basic Requirements")
    st.markdown("""
    - **Salary Credit**: Toggle if you have a monthly salary credit
    - **Card Spend**: Enter your estimated monthly credit card spending
    - **Bill Payments**: Select how many bill payments you make monthly through GIRO
    """)
    
    # Step 3
    st.subheader("Step 3: Advanced Requirements (Optional)")
    st.markdown("""
    Click on "Advanced Requirements" to specify additional criteria:
    - Insurance products
    - Investment products
    - Increased account balance
    - Wealth growth
    
    These requirements can help you earn bonus interest rates with certain banks.
    """)
    
    # Step 4
    st.subheader("Step 4: Calculate Interest")
    st.markdown("""
    1. Click "Calculate Single Bank Interest"
    2. The calculator will:
        - Compare all available banks
        - Show you the optimal bank choice
        - Display your potential monthly and annual interest
        - Provide detailed breakdowns for each bank
    """)
    
    st.info("💡 **Tip**: Start with the basic requirements first. You can always add advanced requirements later to see how they affect your interest rates!")

if __name__ == "__main__":
    main()
