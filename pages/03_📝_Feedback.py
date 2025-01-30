import streamlit as st
from analytics import (
    identify_user, 
    track_calculation, 
    mp,
    MIXPANEL_ENABLED,
)

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

    st.title("📝 Feedback")
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
                # Track feedback in Mixpanel
                if MIXPANEL_ENABLED:
                    feedback_data = {
                        'rating': rating,
                        'usage': usage,
                        'useful_features': [k for k, v in useful_features.items() if v],
                        'has_suggestions': bool(suggestions.strip()),
                        'has_feedback': bool(feedback.strip()),
                        'provided_email': bool(email.strip())
                    }
                    
                    # Add actual feedback content for analysis
                    if suggestions.strip():
                        feedback_data['suggestions'] = suggestions
                    if feedback.strip():
                        feedback_data['feedback'] = feedback
                    if email.strip():
                        feedback_data['email'] = email

                    mp.track(st.session_state.user_id, 'Feedback Submitted', feedback_data)
                
                st.success("""
                    Thank you for your feedback! We appreciate your help in improving SmartSaverSG.
                    
                    Feel free to check out the [GitHub repository](https://github.com/yourusername/smartsaversg) 
                    if you'd like to contribute or follow the project's development.
                """)
                
            except Exception as e:
                st.error(f"Error submitting feedback: {str(e)}")

    # Add link back to main app
    st.markdown("""
        <div style='position: fixed; bottom: 20px; left: 20px;'>
            <a href="/" style='text-decoration: none;'>
                ← Back to Calculator
            </a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    show_feedback_page()