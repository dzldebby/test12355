import streamlit as st
from analytics import (
    identify_user, 
    track_calculation, 
    mp,
    MIXPANEL_ENABLED,
)
import requests

def show_feedback_page():
    # Page config
    st.set_page_config(
        page_title="Feedback - SmartSaverSG",
        page_icon="",
        layout="wide"
    )

    # Custom CSS
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 1rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("")
    st.write("""
        Help us improve SmartSaverSG! Your feedback is valuable in making this tool more useful for everyone.
        
        This tool was built during Chinese New Year 2024 when I realized many of my relatives were missing out on 
        better interest rates simply because comparing across banks was too troublesome.
    """)
    
    # Feedback form
    with st.form("feedback_form"):
        # Rating
        rating = st.slider(
            "How would you rate your experience?",
            min_value=1,
            max_value=5,
            value=5,
            help="1 = Poor, 5 = Excellent"
        )
        
        # Usage frequency
        usage = st.selectbox(
            "How often do you plan to use SmartSaverSG?",
            options=[
                "This is my first time",
                "Monthly to track interest rates",
                "When I'm planning to change banks",
                "One-time use only",
                "Other"
            ]
        )
        
        # Feature feedback
        st.write("##### Which features did you find most useful?")
        col1, col2 = st.columns(2)
        with col1:
            useful_features = {
                "single_bank": st.checkbox("Single Bank Calculator"),
                "multi_bank": st.checkbox("Multi-Bank Optimizer"),
                "interest_breakdown": st.checkbox("Interest Breakdown"),
                "spend_allocation": st.checkbox("Credit Card Spend Allocation")
            }
        
        # Improvement suggestions
        suggestions = st.text_area(
            "What features would you like to see added?",
            placeholder="Enter your suggestions here..."
        )
        
        # General feedback
        feedback = st.text_area(
            "Any other feedback or comments?",
            placeholder="Enter your feedback here..."
        )

        # Email (optional)
        email = st.text_input(
            "Email (optional)",
            placeholder="Enter your email if you'd like us to follow up",
            help="We'll only use this to respond to your feedback"
        )
        
        # Submit button
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            try:
                # Prepare feedback data
                feedback_data = {
                    'rating': rating,
                    'usage': usage,
                    'useful_features': [k for k, v in useful_features.items() if v],
                    'suggestions': suggestions,
                    'feedback': feedback,
                    'email': email
                }
                
                # Send to FormSpree
                response = requests.post(
                    'https://formspree.io/f/xanqjlrb',  # Replace with your FormSpree form ID
                    json=feedback_data
                )
                
                if response.status_code == 200:
                    # Track in Mixpanel if enabled
                    if MIXPANEL_ENABLED:
                        mp.track('Feedback Submitted', feedback_data)
                    
                    st.success("Thank you for your feedback! We appreciate your input.")
                else:
                    st.error("There was an error submitting your feedback. Please try again later.")
                
            except Exception as e:
                st.error(f"There was an error submitting your feedback. Please try again later.")
                print(f"Error saving feedback: {str(e)}")

if __name__ == "__main__":
    show_feedback_page()