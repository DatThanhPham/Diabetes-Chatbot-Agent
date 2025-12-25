"""
Assessment Card Components
"""
import streamlit as st
from utils.helpers import format_date, get_risk_level_info, format_risk_score, format_metric_value
from utils.session_state import navigate_to, set_current_assessment_id

def render_assessment_summary(assessment):
    """Render compact assessment summary for sidebar"""
    
    risk_info = get_risk_level_info(assessment.get('risk_level', 'low'))
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {risk_info['bg_color']} 0%, {risk_info['color']}22 100%);
        border-left: 5px solid {risk_info['color']};
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    ">
        <p style="margin: 0; font-size: 0.85rem; color: #666;">
            📅 {format_date(assessment.get('measured_at'))}
        </p>
        <h3 style="margin: 0.5rem 0; color: {risk_info['color']};">
            {risk_info['label']}
        </h3>
        <p style="margin: 0; font-size: 1.5rem; font-weight: bold; color: {risk_info['color']};">
            {format_risk_score(assessment.get('risk_score', 0))}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    metrics = assessment.get('metrics', {})
    
    st.markdown("#### 📊 Chỉ số chính")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bmi = metrics.get('BMI', 0)
        st.metric("BMI", f"{bmi:.1f}" if bmi else "N/A")
        st.metric("Huyết áp", "Cao" if metrics.get('HighBP') == 1 else "Bình thường")
    
    with col2:
        st.metric("Cholesterol", "Cao" if metrics.get('HighChol') == 1 else "Bình thường")
        st.metric("Vận động", "Có" if metrics.get('PhysActivity') == 1 else "Không")

def render_assessment_card(assessment, user):
    """Render full assessment card for history page"""
    
    risk_info = get_risk_level_info(assessment.get('risk_level', 'low'))
    
    # Card container with border
    st.markdown(f"""
    <div style="
        border: 2px solid {risk_info['color']};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background-color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    ">
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"### {risk_info['label'].split()[0]} Đánh giá ngày {format_date(assessment.get('measured_at'))}")
        if assessment.get('is_valid', True):
            st.markdown("✅ **Hiệu lực**")
        else:
            st.markdown("⚠️ *Đã hết hiệu lực*")
    
    with col2:
        st.markdown(f"""
        <div style="
            text-align: center; 
            padding: 1rem; 
            background: linear-gradient(135deg, {risk_info['bg_color']} 0%, {risk_info['color']}22 100%);
            border-radius: 8px;
            border: 2px solid {risk_info['color']};
        ">
            <p style="margin: 0; font-size: 0.8rem; color: #666;">Nguy cơ</p>
            <p style="margin: 0; font-size: 1.8rem; font-weight: bold; color: {risk_info['color']};">
                {format_risk_score(assessment.get('risk_score', 0))}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("💬 Chat", key=f"chat_{assessment.get('id')}", use_container_width=True, type="primary"):
            set_current_assessment_id(assessment.get('id'))
            navigate_to("Chatbot AI")
            st.rerun()
    
    # Metrics
    st.markdown("#### 📊 Chỉ số sức khỏe")
    
    metrics = assessment.get('metrics', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bmi = metrics.get('BMI', 0)
        st.metric("BMI", f"{bmi:.1f}" if bmi else "N/A")
        age = metrics.get('Age', 0)
        st.metric("Tuổi", f"Nhóm {int(age)}" if age else "N/A")
    
    with col2:
        st.metric("Huyết áp cao", format_metric_value('HighBP', metrics.get('HighBP')))
        st.metric("Cholesterol cao", format_metric_value('HighChol', metrics.get('HighChol')))
    
    with col3:
        st.metric("Hút thuốc", format_metric_value('Smoker', metrics.get('Smoker')))
        st.metric("Vận động", format_metric_value('PhysActivity', metrics.get('PhysActivity')))
    
    with col4:
        gen_hlth = metrics.get('GenHlth', 0)
        st.metric("Sức khỏe TQ", f"{int(gen_hlth)}/5" if gen_hlth else "N/A")
        st.metric("Giới tính", "Nam" if metrics.get('Sex') == 1 else "Nữ")
    
    st.markdown("</div>", unsafe_allow_html=True)