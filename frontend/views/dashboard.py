"""
Dashboard page
"""
import streamlit as st
from services.assessment_service import get_user_assessments
from utils.helpers import get_risk_level_info, format_date, format_risk_score
from utils.session_state import navigate_to
import plotly.graph_objects as go

def show_dashboard(user):
    """Display dashboard"""
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">📊 Dashboard</h1>', unsafe_allow_html=True)
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
            # FIX: Add unique key
            if st.button("📝 Bắt đầu đánh giá", use_container_width=True, type="primary", key="dashboard_start_assessment"):
                navigate_to("Đánh giá mới")
                st.rerun()
        return
    
    # Has assessments - show dashboard
    valid_assessments = [a for a in assessments if a.get('is_valid', True)]
    latest_assessment = valid_assessments[0] if valid_assessments else assessments[0]
    
    st.markdown("### 🎯 Tình trạng hiện tại")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Tổng số đánh giá", len(assessments))
    
    with col2:
        risk_info = get_risk_level_info(latest_assessment.get('risk_level', 'low'))
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background-color: {risk_info['bg_color']}; border-radius: 8px;">
            <p style="margin: 0; color: #666;">Nguy cơ hiện tại</p>
            <h2 style="margin: 0; color: {risk_info['color']};">{risk_info['label']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.metric("📊 Điểm nguy cơ", format_risk_score(latest_assessment.get('risk_score', 0)))
    
    # Latest assessment details
    st.markdown("---")
    st.markdown("### 📋 Đánh giá gần nhất")
    
    risk_info = get_risk_level_info(latest_assessment.get('risk_level', 'low'))
    
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
        <p><strong>📊 Điểm nguy cơ:</strong> {format_risk_score(latest_assessment.get('risk_score', 0))}</p>
        <p style="margin-bottom: 0;">{risk_info['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    st.markdown("#### 🔍 Chỉ số sức khỏe chính")
    
    metrics = latest_assessment.get('metrics', {})
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bmi = metrics.get('BMI', 0)
        st.metric("BMI", f"{bmi:.1f}" if bmi else "N/A")
    
    with col2:
        st.metric("Huyết áp cao", "✓ Có" if metrics.get('HighBP') == 1 else "✗ Không")
    
    with col3:
        st.metric("Cholesterol cao", "✓ Có" if metrics.get('HighChol') == 1 else "✗ Không")
    
    with col4:
        st.metric("Vận động", "✓ Có" if metrics.get('PhysActivity') == 1 else "✗ Không")
    
    # Chart if multiple assessments
    if len(assessments) > 1:
        st.markdown("---")
        st.markdown("### 📈 Xu hướng nguy cơ")
        
        sorted_assessments = sorted(assessments, key=lambda x: x.get('measured_at', ''))
        dates = [format_date(a.get('measured_at')) for a in sorted_assessments]
        scores = [a.get('risk_score', 0) * 100 for a in sorted_assessments]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=scores,
            mode='lines+markers',
            name='Điểm nguy cơ',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=10, color=scores, colorscale='RdYlGn_r', showscale=True)
        ))
        
        fig.add_hline(y=50, line_dash="dash", line_color="red", 
                     annotation_text="Ngưỡng nguy cơ cao (50%)")
        
        fig.update_layout(
            title="Biến đổi điểm nguy cơ theo thời gian",
            xaxis_title="Ngày đánh giá",
            yaxis_title="Điểm nguy cơ (%)",
            height=400,
            hovermode='x unified',
            yaxis=dict(range=[0, 100])
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
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