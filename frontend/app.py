"""
Diabetes Chatbot Agent - Streamlit Frontend
"""
import streamlit as st
import base64

# Page config MUST be first
st.set_page_config(
    page_title="Diabetes Chatbot Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import - CHANGED from pages.* to views.*
from utils.session_state import init_session_state, is_logged_in, get_user, logout
from components.auth import show_auth_page
from views.dashboard import show_dashboard
from views.chatbot import show_chatbot
from views.assessment_form import show_assessment_form
from views.history import show_history
from views.general import show_visualize

# Background image helper
def get_base64_of_image(img_path: str) -> str:
    """Convert image to base64"""
    try:
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

IMAGE_PATH = "./background.jpg"
img_base64 = get_base64_of_image(IMAGE_PATH)

# Custom CSS
# Custom CSS
st.markdown(f"""
<style>
    /* CRITICAL: Hide Streamlit default page navigation */
    section[data-testid="stSidebarNav"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Sidebar gradient */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #ffffff 0%, #e3f2fd 100%) !important;
    }}
    
    /* Background image */
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* Main content container */
    .block-container {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        margin-top: 1rem;
    }}
    
    /* Button styling */
    .stButton > button {{
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    
    /* Primary button (active menu) */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #7c8ff0 0%, #8a5bb0 100%) !important;
    }}
    
    /* Secondary button (inactive menu) */
    .stButton > button[kind="secondary"] {{
        background: white !important;
        border: 2px solid rgba(102, 126, 234, 0.3) !important;
        color: #333 !important;
        font-weight: 600 !important;
    }}
    
    .stButton > button[kind="secondary"]:hover {{
        background: rgba(102, 126, 234, 0.1) !important;
        border: 2px solid rgba(102, 126, 234, 0.5) !important;
        color: #667eea !important;
    }}
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {{
        border-radius: 8px;
        border: 2px solid #e0e0e0;
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: bold;
    }}
    
    /* Form */
    .stForm {{
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

def main():
    """Main application"""
    
    # Check authentication
    if not is_logged_in():
        show_auth_page()
        return
    
    user = get_user()

    # user = {
    #     "id": "692c1c7b48e77a615327f0df",
    #     "name": "Nguyễn Văn A",
    # }
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 0;">
            <h1 style="font-size: 3rem; margin: 0;">🏥</h1>
            <h2 style="font-size: 1.4rem; margin: 0.5rem 0; font-weight: bold;">
                Diabetes Agent
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            border: 2px solid #667eea44;
        ">
            <p style="margin: 0; font-size: 0.85rem; opacity: 0.7;">Xin chào,</p>
            <h3 style="margin: 0.3rem 0 0 0; font-size: 1.3rem; font-weight: bold;">
                👋 {user.get('name', 'User')}
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📋 MENU")
        
        # Menu navigation with buttons
        menu_pages = {
            "Tổng quan": "📈",
            "Dashboard": "📊",
            "Đánh giá mới": "📝",
            "Chatbot AI": "💬",
            "Lịch sử đánh giá": "📜"
        }
        
        for page_name, icon in menu_pages.items():
            is_current = st.session_state.current_page == page_name
            button_type = "primary" if is_current else "secondary"
            
            # Use unique key with timestamp to avoid conflicts
            if st.button(
                f"{icon} {page_name}",
                key=f"menu_btn_{page_name.replace(' ', '_')}",
                type=button_type,
                use_container_width=True
            ):
                st.session_state.current_page = page_name
                st.rerun()
        
        st.markdown("---")
        
        # User info
        with st.expander("ℹ️ Thông tin tài khoản"):
            user_id = user.get('id', '')
            st.markdown(f"""
            **User ID:** `{user_id[:12]}...`  
            **Username:** `{user.get('name', '')}`
            """)
        
        st.markdown("<br>" * 4, unsafe_allow_html=True)
        
        # Logout
        if st.button("🚪 Đăng xuất", key="logout_btn", use_container_width=True, type="secondary"):
            logout()
            st.rerun()
    
    # Route to correct page
    current_page = st.session_state.current_page
    
    if current_page == "Tổng quan":
        show_visualize(user)
    elif current_page == "Dashboard":
        show_dashboard(user)
    elif current_page == "Đánh giá mới":
        show_assessment_form(user)
    elif current_page == "Chatbot AI":
        show_chatbot(user)
    elif current_page == "Lịch sử đánh giá":
        show_history(user)

if __name__ == "__main__":
    main()