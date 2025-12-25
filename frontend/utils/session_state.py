"""
Session state management
"""
import streamlit as st
from services.api_client import api_client
from services.auth_service import (
    refresh_access_token,
    get_current_user,
    logout_user,
)

def _init_auth_from_cookie():
    """
    Try to reconnect:

    1. If exist user + access_token in session_state -> just need to set header for APIClient.
    2. If didn't exist -> try to use refresh token in cookie (between Streamlit & Flask):
       - Fetch /users/refresh -> retrieve new access token lấy access token mới
       - Fetch /users/me -> retrieve user information
    """
    # If user stayed in session -> set header
    user = st.session_state.get("user")
    access_token = st.session_state.get("access_token")

    if user and access_token:
        api_client.set_auth_token(access_token)
        # Check flag
        st.session_state.logged_in = True
        return

    # 2. If don't -> try to refresh in case cookie is still living
    refresh_result = refresh_access_token()
    if not refresh_result.get("success") or not refresh_result.get("access_token"):
        # Can't refresh -> login
        return

    new_access = refresh_result["access_token"]
    api_client.set_auth_token(new_access)

    user_result = get_current_user()
    if not user_result.get("success"):
        return

    st.session_state["user"] = user_result["data"]
    st.session_state["access_token"] = new_access
    # Turn on the flag
    st.session_state["logged_in"] = True


def init_session_state():
    """Initialize session state variables"""
    
    # User authentication
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
        
    # Bootstrap auth
    if "auth_bootstrapped" not in st.session_state:
        st.session_state["auth_bootstrapped"] = True
        _init_auth_from_cookie()
    
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
    """Set logged in user (dùng sau khi login thành công)"""
    st.session_state.user = user_data
    st.session_state.logged_in = True


def logout():
    """Logout user"""
    logout_user()

    st.session_state.user = None
    st.session_state.logged_in = False
    st.session_state.current_page = "Dashboard"
    st.session_state.current_assessment_id = None
    st.session_state.assessment_result = None
    st.session_state.chat_messages = []
    st.session_state.last_assessment_id = None
    st.session_state.access_token = None


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
