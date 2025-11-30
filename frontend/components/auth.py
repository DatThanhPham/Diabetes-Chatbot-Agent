"""
Authentication components
"""
import streamlit as st
from services.auth_service import register_user, login_user
from utils.session_state import set_user

def show_login_form():
    """Display login form"""
    st.subheader("🔐 Đăng nhập")
    
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập", key="login_username")
        password = st.text_input("Mật khẩu", type="password", key="login_password")
        
        col1, col2 = st.columns([1, 3])
        with col1:
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
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #1f77b4; font-size: 3rem; margin-bottom: 0.5rem;">
            🏥 Diabetes Chatbot Agent
        </h1>
        <p style="color: #666; font-size: 1.2rem;">
            Hệ thống tư vấn và dự đoán nguy cơ tiểu đường
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký"])
    
    with tab1:
        show_login_form()
        
        st.markdown("---")
        st.info("💡 **Tài khoản demo:**\n- Username: `demo_user`\n- Password: `demo123`")
    
    with tab2:
        show_register_form()
        
        st.markdown("---")
        st.info("ℹ️ Sau khi đăng ký, bạn sẽ được tự động đăng nhập.")