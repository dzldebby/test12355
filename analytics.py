import streamlit as st
from datetime import datetime
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add a StreamHandler to also show logs in Streamlit
streamlit_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(streamlit_handler)

try:
    logger.info("Attempting to import mixpanel...")
    import mixpanel
    logger.info("Mixpanel import successful")
    
    logger.info("Attempting to get Mixpanel token from secrets...")
    token = st.secrets["mixpanel"]["token"]
    logger.info("Successfully retrieved Mixpanel token")
    
    logger.info("Initializing Mixpanel...")
    mp = mixpanel.Mixpanel(token)
    MIXPANEL_ENABLED = True
    logger.info("Mixpanel initialization successful")
    
except ImportError as e:
    logger.error(f"Failed to import mixpanel: {str(e)}")
    MIXPANEL_ENABLED = False
except KeyError as e:
    logger.error(f"Failed to get Mixpanel token from secrets: {str(e)}")
    MIXPANEL_ENABLED = False
except Exception as e:
    logger.error(f"Unexpected error during Mixpanel setup: {str(e)}")
    MIXPANEL_ENABLED = False

def get_user_id():
    """Get user ID from session state, initializing if needed"""
    try:
        logger.info("Getting user ID...")
        if 'user_id' not in st.session_state:
            logger.info("Generating new user ID...")
            try:
                # Log the experimental_user object
                logger.info(f"experimental_user object: {st.experimental_user}")
                user_hash = st.experimental_user.hash
                logger.info(f"Generated hash: {user_hash}")
                st.session_state.user_id = str(user_hash)
                logger.info(f"Generated user ID: {st.session_state.user_id}")
            except AttributeError as e:
                logger.error(f"AttributeError accessing experimental_user: {str(e)}")
                # Fallback to a random ID if experimental_user fails
                import uuid
                fallback_id = str(uuid.uuid4())
                logger.info(f"Using fallback ID: {fallback_id}")
                st.session_state.user_id = fallback_id
            except Exception as e:
                logger.error(f"Unexpected error generating user ID: {type(e).__name__}: {str(e)}")
                raise
        return st.session_state.user_id
    except Exception as e:
        logger.error(f"Error in get_user_id: {type(e).__name__}: {str(e)}")
        # Include traceback in logs
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "unknown_user"

def identify_user():
    """Generate and track unique user ID"""
    try:
        logger.info("Identifying user...")
        user_id = get_user_id()
        
        if MIXPANEL_ENABLED and 'mixpanel_initialized' not in st.session_state:
            logger.info("Setting up Mixpanel user profile...")
            mp.people_set(user_id, {
                'first_visit': str(datetime.now()),
                'platform': 'Streamlit'
            })
            mp.track(user_id, 'First Visit')
            st.session_state.mixpanel_initialized = True
            logger.info("Mixpanel user profile setup complete")
        return user_id
    except Exception as e:
        logger.error(f"Error in identify_user: {str(e)}")
        return "unknown_user"

def track_error(error_type, error_message):
    """Track when errors occur"""
    try:
        if MIXPANEL_ENABLED:
            logger.info(f"Tracking error: {error_type}")
            user_id = get_user_id()
            mp.track(user_id, 'Error Occurred', {
                'type': error_type,
                'message': error_message,
                'variant': st.session_state.get('variant', 'unknown')
            })
    except Exception as e:
        logger.error(f"Error in track_error: {str(e)}")

def track_calculation(calc_type, amount, requirements):
    """Track when user performs a calculation"""
    try:
        if MIXPANEL_ENABLED:
            logger.info(f"Tracking calculation: {calc_type}")
            user_id = get_user_id()
            mp.track(user_id, 'Calculation Performed', {
                'type': calc_type,
                'amount': amount,
                'has_salary': requirements['has_salary'],
                'salary_amount': requirements['salary_amount'],
                'spend_amount': requirements['spend_amount'],
                'variant': st.session_state.get('variant', 'unknown')
            })
    except Exception as e:
        logger.error(f"Error in track_calculation: {str(e)}")

def track_bank_interaction(bank_name, action):
    """Track when user interacts with bank details"""
    try:
        if MIXPANEL_ENABLED:
            logger.info(f"Tracking bank interaction: {bank_name} - {action}")
            user_id = get_user_id()
            mp.track(user_id, 'Bank Interaction', {
                'bank': bank_name,
                'action': action,
                'variant': st.session_state.get('variant', 'unknown')
            })
    except Exception as e:
        logger.error(f"Error in track_bank_interaction: {str(e)}")

def assign_variant():
    """Assign user to A/B test variant"""
    try:
        logger.info("Assigning variant...")
        if 'variant' not in st.session_state:
            user_id = get_user_id()
            variant = 'A' if hash(user_id) % 2 == 0 else 'B'
            st.session_state.variant = variant
            logger.info(f"Assigned variant: {variant}")
            
            if MIXPANEL_ENABLED:
                mp.track(user_id, 'Assigned Variant', {
                    'variant': variant
                })
        return st.session_state.variant
    except Exception as e:
        logger.error(f"Error in assign_variant: {str(e)}")
        return 'A'  # Default to A if there's an error