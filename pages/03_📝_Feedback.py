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
        page_icon="📝",
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

    st.title("📝 Quick Feedback")
    st.write("Help us improve SmartSaverSG with your feedback!")
    
    # Feedback form
    with st.form("feedback_form"):
        # NPS Score
        nps = st.slider(
            "How likely are you to recommend SmartSaverSG to a friend or colleague?",
            min_value=0,
            max_value=10,
            value=8,
            help="0 = Not at all likely, 10 = Extremely likely"
        )
        
        # User Experience
        experience = st.radio(
            "How easy was it to use SmartSaverSG?",
            options=[
                "Very Easy",
                "Easy",
                "Neutral",
                "Difficult",
                "Very Difficult"
            ]
        )
        
        # Open feedback
        feedback = st.text_area(
            "What could we improve?",
            placeholder="Share your suggestions here...",
            help="Optional: Tell us what would make SmartSaverSG more useful for you"
        )
        
        # Submit button
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            try:
                # Prepare feedback data
                feedback_data = {
                    'nps_score': nps,
                    'ease_of_use': experience,
                    'improvement_suggestions': feedback
                }
                
                # Send to FormSpree
                response = requests.post(
                    'https://formspree.io/f/xanqjlrb',
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