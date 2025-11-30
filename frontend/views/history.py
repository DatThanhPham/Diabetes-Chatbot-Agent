"""
Assessment History Page
"""
import streamlit as st  # ✅ THÊM DÒNG NÀY
import plotly.graph_objects as go
import pandas as pd
from services.assessment_service import get_user_assessments
from components.assessment_card import render_assessment_card
from utils.helpers import format_date, get_risk_level_info, format_risk_score
from utils.session_state import navigate_to

def show_history(user):
    """Display assessment history with charts and filters"""
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">📈 Lịch sử đánh giá</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Get all assessments
    result = get_user_assessments(user['id'])
    
    if not result['success']:
        st.error(f"❌ Lỗi: {result['error']}")
        return
    
    assessments = result['data']
    
    if not assessments:
        st.info("📭 Bạn chưa có đánh giá nào!")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📝 Tạo đánh giá đầu tiên", use_container_width=True, type="primary"):
                navigate_to("Đánh giá mới")
                st.rerun()
        return
    
    # Statistics
    st.markdown("### 📊 Thống kê tổng quan")
    
    total = len(assessments)
    high_risk_count = sum(1 for a in assessments if a.get('risk_level') == 'high')
    low_risk_count = total - high_risk_count
    avg_score = sum(a.get('risk_score', 0) for a in assessments) / total
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Tổng số đánh giá", total)
    
    with col2:
        st.metric("⚠️ Nguy cơ cao", high_risk_count, 
                  delta=None if high_risk_count == 0 else f"{high_risk_count/total*100:.0f}%")
    
    with col3:
        st.metric("✅ Nguy cơ thấp", low_risk_count,
                  delta=None if low_risk_count == 0 else f"{low_risk_count/total*100:.0f}%")
    
    with col4:
        st.metric("📊 Điểm TB", format_risk_score(avg_score))
    
    # Risk trend chart
    if len(assessments) > 1:
        st.markdown("---")
        st.markdown("### 📈 Xu hướng nguy cơ theo thời gian")
        
        # Sort by date
        sorted_assessments = sorted(assessments, key=lambda x: x.get('measured_at', ''))
        
        dates = [format_date(a.get('measured_at')) for a in sorted_assessments]
        scores = [a.get('risk_score', 0) * 100 for a in sorted_assessments]
        colors = ['#f44336' if a.get('risk_level') == 'high' else '#4caf50' for a in sorted_assessments]
        
        fig = go.Figure()
        
        # Line + scatter
        fig.add_trace(go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            name='Điểm nguy cơ',
            line=dict(color='#1f77b4', width=3),
            marker=dict(
                size=14, 
                color=colors,
                line=dict(width=2, color='white'),
                symbol='circle'
            ),
            hovertemplate='<b>%{x}</b><br>Điểm nguy cơ: %{y:.1f}%<extra></extra>'
        ))
        
        # Threshold line
        fig.add_hline(
            y=50, 
            line_dash="dash", 
            line_color="red",
            line_width=2,
            annotation_text="Ngưỡng nguy cơ cao (50%)",
            annotation_position="right"
        )
        
        fig.update_layout(
            title={
                'text': "Biến đổi điểm nguy cơ",
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Thời gian",
            yaxis_title="Điểm nguy cơ (%)",
            height=450,
            hovermode='x unified',
            yaxis=dict(range=[0, 100]),
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # BMI trend
        st.markdown("### 📊 Xu hướng BMI")
        
        bmis = [a.get('metrics', {}).get('BMI', 0) for a in sorted_assessments]
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=dates,
            y=bmis,
            mode='lines+markers',
            name='BMI',
            line=dict(color='#ff9800', width=3),
            marker=dict(size=12, color='#ff9800'),
            hovertemplate='<b>%{x}</b><br>BMI: %{y:.1f}<extra></extra>'
        ))
        
        # BMI ranges with annotations
        fig2.add_hrect(y0=18.5, y1=24.9, fillcolor="green", opacity=0.1, 
                       annotation_text="Bình thường", annotation_position="right")
        fig2.add_hrect(y0=25, y1=29.9, fillcolor="orange", opacity=0.1, 
                       annotation_text="Thừa cân", annotation_position="right")
        fig2.add_hrect(y0=30, y1=50, fillcolor="red", opacity=0.1, 
                       annotation_text="Béo phì", annotation_position="right")
        
        fig2.update_layout(
            title={
                'text': "Biến đổi BMI",
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Thời gian",
            yaxis_title="BMI",
            height=450,
            hovermode='x unified',
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # Assessment list with filters
    st.markdown("---")
    st.markdown("### 📋 Danh sách đánh giá")
    
    # Filter and sort options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filter_option = st.radio(
            "Lọc theo:",
            ["Tất cả", "Nguy cơ cao", "Nguy cơ thấp", "Chỉ hiệu lực"],
            horizontal=True,
            key="filter_radio"
        )
    
    with col2:
        sort_option = st.selectbox(
            "Sắp xếp:",
            ["Mới nhất", "Cũ nhất", "Nguy cơ cao → thấp", "Nguy cơ thấp → cao"],
            key="sort_select"
        )
    
    # Apply filters
    filtered = assessments.copy()
    
    if filter_option == "Nguy cơ cao":
        filtered = [a for a in filtered if a.get('risk_level') == 'high']
    elif filter_option == "Nguy cơ thấp":
        filtered = [a for a in filtered if a.get('risk_level') == 'low']
    elif filter_option == "Chỉ hiệu lực":
        filtered = [a for a in filtered if a.get('is_valid', True)]
    
    # Apply sorting
    if sort_option == "Mới nhất":
        filtered.sort(key=lambda x: x.get('measured_at', ''), reverse=True)
    elif sort_option == "Cũ nhất":
        filtered.sort(key=lambda x: x.get('measured_at', ''))
    elif sort_option == "Nguy cơ cao → thấp":
        filtered.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
    else:
        filtered.sort(key=lambda x: x.get('risk_score', 0))
    
    st.markdown(f"*Hiển thị **{len(filtered)}** / **{len(assessments)}** đánh giá*")
    
    st.markdown("---")
    
    # Display cards
    if not filtered:
        st.info("ℹ️ Không có đánh giá nào phù hợp với bộ lọc!")
    else:
        for i, assessment in enumerate(filtered):
            render_assessment_card(assessment, user)
            
            # Add separator except for last item
            if i < len(filtered) - 1:
                st.markdown("<br>", unsafe_allow_html=True)