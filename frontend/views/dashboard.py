"""
Dashboard page
"""
import streamlit as st
from services.assessment_service import get_user_assessments
from utils.helpers import get_risk_level_info, format_date, format_risk_score
from utils.session_state import navigate_to
import base64
import os

def get_base64_image(image_path):
    """Convert image to base64"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Không thể load ảnh: {e}")
        return None

def show_dashboard(user):
    """Display dashboard"""
    
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
    
    /* Make containers transparent */
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
    
    /* Add overlay for better readability */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.4);
        z-index: 0;
        pointer-events: none;
    }}
    
    .main > div {{
        position: relative;
        z-index: 1;
    }}
    
    /* Style for content cards */
    .element-container {{
        background-color: transparent !important;
    }}
    
    /* Style metrics with semi-transparent background */
    [data-testid="stMetric"] {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    /* Style buttons */
    .stButton > button {{
        background-color: rgba(31, 119, 180, 0.95) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }}
    </style>
    """ if base64_image else ""
    
    st.markdown(background_css, unsafe_allow_html=True)
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4; text-shadow: 2px 2px 4px rgba(255,255,255,0.8);">📊 Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Get assessments
    result = get_user_assessments(user['id'])
    
    if not result['success']:
        st.error(f"❌ Lỗi: {result['error']}")
        return
    
    assessments = result['data']
    
    if not assessments:
        # No assessments - welcome screen
        st.info("👋 Chào mừng bạn đến với Diabetes Chatbot Agent!")
        st.warning("⚠️ Bạn chưa có đánh giá sức khỏe nào. Hãy bắt đầu bằng cách điền form đánh giá!")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📝 Bắt đầu đánh giá", use_container_width=True, type="primary", key="dashboard_start_assessment"):
                navigate_to("Đánh giá mới")
                st.rerun()
        return
    
    # Has assessments - show dashboard
    valid_assessments = [a for a in assessments if a.get('is_valid', True)]
    latest_assessment = valid_assessments[0] if valid_assessments else assessments[0]
    
    st.markdown("### 🎯 Tình trạng hiện tại")
    
    col1, col2 = st.columns([0.25, 1.5])
    
    with col1:
        st.metric("📋 Tổng số đánh giá", len(assessments))
    
    with col2:
        prediction = latest_assessment.get('prediction', {})
        risk_level = prediction.get('risk_level', 'low')
        risk_info = get_risk_level_info(risk_level)
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background-color: {risk_info['bg_color']}; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
            <p style="margin: 0; color: #666;">Nguy cơ hiện tại</p>
            <h2 style="margin: 0; color: {risk_info['color']};">{risk_info['label']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Latest assessment details
    st.markdown("---")
    st.markdown("### 📋 Đánh giá gần nhất")
    
    prediction = latest_assessment.get('prediction', {})
    risk_level = prediction.get('risk_level', 'low')
    risk_info = get_risk_level_info(risk_level)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {risk_info['bg_color']} 0%, {risk_info['color']}22 100%);
        border-left: 5px solid {risk_info['color']};
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    ">
        <h3 style="color: {risk_info['color']}; margin-top: 0;">{risk_info['label']}</h3>
        <p><strong>📅 Ngày đánh giá:</strong> {format_date(latest_assessment.get('measured_at'))}</p>
        <p style="margin-bottom: 0;">{risk_info['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    st.markdown("#### 🔍 Chỉ số sức khỏe chính")
    
    metrics = latest_assessment.get('metrics', {})
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bmi = metrics.get('BMI', 0)
        # Determine BMI category
        if bmi >= 30:
            bmi_color = "#ff4444"  # Red - Obese
            bmi_bg = "#ffebee"
        elif bmi >= 25:
            bmi_color = "#ff9800"  # Orange - Overweight
            bmi_bg = "#fff3e0"
        elif bmi >= 18.5:
            bmi_color = "#4caf50"  # Green - Normal
            bmi_bg = "#e8f5e9"
        else:
            bmi_color = "#2196f3"  # Blue - Underweight
            bmi_bg = "#e3f2fd"
        
        st.markdown(f"""
        <div style="
            background-color: {bmi_bg};
            border: 2px solid {bmi_color};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        ">
            <p style="margin: 0; color: #666; font-size: 0.9rem;">BMI</p>
            <h2 style="margin: 0.5rem 0 0 0; color: {bmi_color};">{bmi:.1f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        high_bp = metrics.get('HighBP', 0)
        bp_color = "#ff4444" if high_bp == 1 else "#4caf50"
        bp_bg = "#ffebee" if high_bp == 1 else "#e8f5e9"
        bp_text = "Có" if high_bp == 1 else "Không"
        
        st.markdown(f"""
        <div style="
            background-color: {bp_bg};
            border: 2px solid {bp_color};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        ">
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Huyết áp cao</p>
            <h2 style="margin: 0.5rem 0 0 0; color: {bp_color};">{bp_text}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        high_chol = metrics.get('HighChol', 0)
        chol_color = "#ff4444" if high_chol == 1 else "#4caf50"
        chol_bg = "#ffebee" if high_chol == 1 else "#e8f5e9"
        chol_text = "Có" if high_chol == 1 else "Không"
        
        st.markdown(f"""
        <div style="
            background-color: {chol_bg};
            border: 2px solid {chol_color};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        ">
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Cholesterol cao</p>
            <h2 style="margin: 0.5rem 0 0 0; color: {chol_color};">{chol_text}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        phys_activity = metrics.get('PhysActivity', 0)
        activity_color = "#4caf50" if phys_activity == 1 else "#ff4444"
        activity_bg = "#e8f5e9" if phys_activity == 1 else "#ffebee"
        activity_text = "Có" if phys_activity == 1 else "Không"
        
        st.markdown(f"""
        <div style="
            background-color: {activity_bg};
            border: 2px solid {activity_color};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        ">
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Vận động</p>
            <h2 style="margin: 0.5rem 0 0 0; color: {activity_color};">{activity_text}</h2>
        </div>
        """, unsafe_allow_html=True)

    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Thao tác nhanh")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💬 Chat với AI", use_container_width=True, type="primary", key="dashboard_go_chat"):
            navigate_to("Chatbot AI")
            st.rerun()
    
    with col2:
        if st.button("📝 Đánh giá lại", use_container_width=True, key="dashboard_go_assess"):
            navigate_to("Đánh giá mới")
            st.rerun()
    
    with col3:
        if st.button("📜 Xem lịch sử", use_container_width=True, key="dashboard_go_history"):
            navigate_to("Lịch sử đánh giá")
            st.rerun()