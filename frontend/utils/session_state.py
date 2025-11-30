"""
Session state management
"""
import streamlit as st

def init_session_state():
    """Initialize session state variables"""
    
    # User authentication
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Navigation - changed from 'menu' to 'current_page'
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    # Assessment data
    if 'current_assessment_id' not in st.session_state:
        st.session_state.current_assessment_id = None
    
    if 'assessment_result' not in st.session_state:
        st.session_state.assessment_result = None
    
    # Chat
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'last_assessment_id' not in st.session_state:
        st.session_state.last_assessment_id = None

def get_user():
    """Get current logged in user"""
    return st.session_state.get('user')

def set_user(user_data):
    """Set logged in user"""
    st.session_state.user = user_data
    st.session_state.logged_in = True

def logout():
    """Logout user"""
    st.session_state.user = None
    st.session_state.logged_in = False
    st.session_state.current_page = "Dashboard"
    st.session_state.current_assessment_id = None
    st.session_state.assessment_result = None
    st.session_state.chat_messages = []
    st.session_state.last_assessment_id = None

def is_logged_in():
    """Check if user is logged in"""
    return st.session_state.get('logged_in', False)

def navigate_to(page_name):
    """Navigate to a page"""
    st.session_state.current_page = page_name

def set_current_assessment_id(assessment_id):
    """Set current assessment ID for chat"""
    st.session_state.current_assessment_id = assessment_id
    # Clear chat messages when switching assessment
    if st.session_state.last_assessment_id != assessment_id:
        st.session_state.chat_messages = []
        st.session_state.last_assessment_id = assessment_id

def get_current_assessment_id():
    """Get current assessment ID"""
    return st.session_state.get('current_assessment_id')

def set_assessment_result(result):
    """Save assessment result"""
    st.session_state.assessment_result = result

def get_assessment_result():
    """Get current assessment result"""
    return st.session_state.get('assessment_result')