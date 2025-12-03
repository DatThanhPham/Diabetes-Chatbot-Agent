"""
Authentication components
"""
import base64
import os
import streamlit as st
from services.auth_service import register_user, login_user
from utils.session_state import set_user

def get_base64_image(image_path):
    """Convert image to base64"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Không thể load ảnh: {e}")
        return None


def show_login_form():
    """Display login form"""
    st.subheader("🔐 Đăng nhập")
    
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập", key="login_username")
        password = st.text_input("Mật khẩu", type="password", key="login_password")
        
        col1, col2, col3 = st.columns([1, 3, 1  ])
        with col2:
            submit = st.form_submit_button("Đăng nhập", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("❌ Vui lòng nhập đầy đủ thông tin!")
                return False
            
            with st.spinner("🔄 Đang đăng nhập..."):
                result = login_user(username, password)
            
            if result['success']:
                set_user(result['data']['user'])
                st.success("✅ Đăng nhập thành công!")
                st.balloons()
                st.rerun()
                return True
            else:
                st.error(f"❌ {result['error']}")
                return False
    
    return False

def show_register_form():
    """Display register form"""
    st.subheader("📝 Đăng ký tài khoản")
    
    with st.form("register_form"):
        username = st.text_input("Tên đăng nhập", key="register_username")
        password = st.text_input("Mật khẩu", type="password", key="register_password")
        confirm_password = st.text_input("Xác nhận mật khẩu", type="password", key="register_confirm")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submit = st.form_submit_button("Đăng ký", use_container_width=True)
        
        if submit:
            if not username or not password or not confirm_password:
                st.error("❌ Vui lòng nhập đầy đủ thông tin!")
                return False
            
            if password != confirm_password:
                st.error("❌ Mật khẩu không khớp!")
                return False
            
            if len(password) < 6:
                st.error("❌ Mật khẩu phải có ít nhất 6 ký tự!")
                return False
            
            with st.spinner("🔄 Đang đăng ký..."):
                result = register_user(username, password)
            
            if result['success']:
                st.success("✅ Đăng ký thành công! Đang đăng nhập...")
                
                # Auto login
                login_result = login_user(username, password)
                if login_result['success']:
                    set_user(login_result['data']['user'])
                    st.balloons()
                    st.rerun()
                return True
            else:
                st.error(f"❌ {result['error']}")
                return False
    
    return False

def show_auth_page():
    """Display authentication page with tabs"""
    
    # Get background image
    image_path = os.path.join(os.path.dirname(__file__), "..", "assets", "background.jpg")
    base64_image = get_base64_image(image_path)
    
    # Custom CSS for background and styling
    background_css = f"""
    <style>
    /* Background image */
    .stApp {{
        background-image: url('data:image/jpeg;base64,{base64_image}');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* Make ALL containers transparent */
    .main {{
        background-color: transparent !important;
    }}
    
    .block-container {{
        background-color: transparent !important;
        padding-top: 2rem;
    }}
    
    [data-testid="stVerticalBlock"] {{
        background-color: transparent !important;
    }}
    
    [data-testid="stHorizontalBlock"] {{
        background-color: transparent !important;
    }}
    
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.3);
        z-index: 0;
        pointer-events: none;
    }}
    
    .main > div {{
        position: relative;
        z-index: 1;
    }}
    
    .stTabs [data-baseweb="tab-panel"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }}
    
    .stTabs {{
        background-color: transparent !important;
    }}
    
    [data-baseweb="tab-list"] {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 10px 10px 0 0;
        padding: 0.5rem;
    }}
    
    .element-container {{
        background-color: transparent !important;
    }}
    </style>
    """ if base64_image else ""
    
    st.markdown(background_css, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; position: relative; z-index: 1;">
        <h1 style="color: #1f77b4; font-size: 3rem; margin-bottom: 0.5rem; text-shadow: 2px 2px 4px rgba(255,255,255,0.8);">
            🏥 Diabetes Chatbot Agent
        </h1>
        <p style="color: #333; font-size: 1.2rem; text-shadow: 1px 1px 2px rgba(255,255,255,0.8);">
            Hệ thống tư vấn và dự đoán nguy cơ tiểu đường
        </p>
        <p style="color: #333; font-size: 1.2rem; font-weight: bold; text-shadow: 1px 1px 2px rgba(255,255,255,0.8);">
            Nhóm Cloud Djata
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Center container with max width
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col3:
        tab1, tab2 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký"])
        
        with tab1:
            show_login_form()
        
        with tab2:
            show_register_form()
            
            st.markdown("---")
            st.info("ℹ️ Sau khi đăng ký, bạn sẽ được tự động đăng nhập.")