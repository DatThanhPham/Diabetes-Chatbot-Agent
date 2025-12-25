"""
Assessment History Page
"""
import streamlit as st
import plotly.graph_objects as go
import base64
import os
from services.assessment_service import get_user_assessments
from utils.helpers import format_date, get_risk_level_info, format_risk_score
from utils.session_state import navigate_to

def get_base64_image(image_path):
    """Convert image to base64"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Không thể load ảnh: {e}")
        return None

def show_history(user):
    """Display assessment history with charts and filters"""
    
    image_path = os.path.join(os.path.dirname(__file__), "..", "assets", "background.jpg")
    base64_image = get_base64_image(image_path)
    
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
    
    /* Style for content */
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
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4; text-shadow: 2px 2px 4px rgba(255,255,255,0.8);">📈 Lịch sử đánh giá</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    result = get_user_assessments(user['id'], valid_only=False)
    
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
    
    for assessment in assessments:
        prediction_data = assessment.get('prediction', {})
        
        if isinstance(prediction_data, dict):
            assessment['prediction_value'] = prediction_data.get('prediction', 0)
            assessment['risk_level'] = prediction_data.get('risk_level', 'low')
        else:
            assessment['prediction_value'] = prediction_data
            assessment['risk_level'] = 'high' if prediction_data == 1 else 'low'
    
    st.markdown("### 📊 Thống kê")
    
    total = len(assessments)
    high_risk = sum(1 for a in assessments if a.get('risk_level') == 'high')
    low_risk = sum(1 for a in assessments if a.get('risk_level') == 'low')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Tổng số đánh giá", total)
    
    with col2:
        st.metric("⚠️ Nguy cơ cao", high_risk,
                  delta=f"{high_risk/total*100:.0f}%" if total > 0 else None,
                  delta_color="inverse")
    
    with col3:
        st.metric("✅ Nguy cơ thấp", low_risk,
                  delta=f"{low_risk/total*100:.0f}%" if total > 0 else None)
    
    if len(assessments) > 1:
        st.markdown("---")
        st.markdown("### 📈 Xu hướng theo thời gian")
        
        chart_data = list(reversed(assessments))
        
        dates = [format_date(a.get('measured_at')) for a in chart_data]
        predictions = [a.get('prediction_value', 0) for a in chart_data]
        colors = ['#f44336' if a.get('risk_level') == 'high' else '#4caf50' for a in chart_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=predictions,
            mode='lines+markers',
            name='Kết quả',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=14, color=colors, line=dict(width=2, color='white')),
            hovertemplate='<b>%{x}</b><br>Kết quả: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': "Kết quả đánh giá",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#1f77b4'}
            },
            xaxis_title="Thời gian",
            yaxis_title="Kết quả",
            height=400,
            template='plotly_white',
            showlegend=False,
            yaxis=dict(
                tickmode='array',
                tickvals=[0, 1],
                ticktext=['Nguy cơ thấp', 'Nguy cơ cao']
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        bmis = [a.get('metrics', {}).get('BMI', 0) for a in chart_data]
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=dates,
            y=bmis,
            mode='lines+markers',
            name='BMI',
            line=dict(color='#ff9800', width=3),
            marker=dict(size=12, color='#ff9800', line=dict(width=2, color='white')),
            hovertemplate='<b>%{x}</b><br>BMI: %{y:.1f}<extra></extra>'
        ))
        
        fig2.add_hrect(y0=0, y1=18.5, fillcolor="lightblue", opacity=0.1, 
                       annotation_text="Thiếu cân", annotation_position="left")
        fig2.add_hrect(y0=18.5, y1=24.9, fillcolor="green", opacity=0.1, 
                       annotation_text="Bình thường", annotation_position="left")
        fig2.add_hrect(y0=25, y1=29.9, fillcolor="orange", opacity=0.1, 
                       annotation_text="Thừa cân", annotation_position="left")
        fig2.add_hrect(y0=30, y1=50, fillcolor="red", opacity=0.1, 
                       annotation_text="Béo phì", annotation_position="left")
        
        fig2.update_layout(
            title={
                'text': "Chỉ số BMI",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#ff9800'}
            },
            xaxis_title="Thời gian",
            yaxis_title="BMI (kg/m²)",
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Chi tiết đánh giá")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filter_opt = st.radio(
            "Lọc:",
            ["Tất cả", "Nguy cơ cao", "Nguy cơ thấp"],
            horizontal=True
        )
    
    with col2:
        sort_opt = st.selectbox("Sắp xếp:", ["Mới nhất", "Cũ nhất"])
    
    filtered = assessments.copy()
    
    if filter_opt == "Nguy cơ cao":
        filtered = [a for a in filtered if a.get('risk_level') == 'high']
    elif filter_opt == "Nguy cơ thấp":
        filtered = [a for a in filtered if a.get('risk_level') == 'low']
    
    if sort_opt == "Cũ nhất":
        filtered.reverse()
    
    st.markdown(f"*Hiển thị **{len(filtered)}** / **{total}** đánh giá*")
    st.markdown("---")
    
    if not filtered:
        st.info("ℹ️ Không có đánh giá nào!")
    else:
        for assessment in filtered:
            prediction = assessment.get('prediction', {})
            risk_level = prediction.get('risk_level', 'low')
            risk_info = get_risk_level_info(risk_level)
            measured_at = assessment.get('measured_at', '')
            metrics = assessment.get('metrics', {})
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {risk_info['bg_color']} 0%, {risk_info['color']}22 100%);
                border-left: 5px solid {risk_info['color']};
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            ">
                <h3 style="margin: 0; color: {risk_info['color']};">
                    {risk_info['label']}
                </h3>
                <p style="margin: 0.5rem 0; color: #666;">
                    📅 {format_date(measured_at)}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔍 Xem chi tiết"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    bmi = metrics.get('BMI', 0)
                    st.metric("BMI", f"{bmi:.1f}")
                
                with col2:
                    bp = "Có" if metrics.get('HighBP') == 1 else "Không"
                    st.metric("Huyết áp cao", bp)
                
                with col3:
                    chol = "Có" if metrics.get('HighChol') == 1 else "Không"
                    st.metric("Cholesterol cao", chol)
                
                with col4:
                    activity = "Có" if metrics.get('PhysActivity') == 1 else "Không"
                    st.metric("Vận động", activity)
                
                st.markdown("#### Thông tin bổ sung")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    age_map = {1:"18-24",2:"25-29",3:"30-34",4:"35-39",5:"40-44",
                              6:"45-49",7:"50-54",8:"55-59",9:"60-64",10:"65-69",
                              11:"70-74",12:"75-79",13:"80+"}
                    age = age_map.get(int(metrics.get('Age', 0)), "N/A")
                    sex = "Nam" if metrics.get('Sex') == 1 else "Nữ"
                    
                    st.write(f"**Tuổi:** {age}")
                    st.write(f"**Giới tính:** {sex}")
                    st.write(f"**Hút thuốc:** {'Có' if metrics.get('Smoker') == 1 else 'Không'}")
                
                with col2:
                    st.write(f"**Bệnh tim:** {'Có' if metrics.get('HeartDiseaseorAttack') == 1 else 'Không'}")
                    st.write(f"**Đột quỵ:** {'Có' if metrics.get('Stroke') == 1 else 'Không'}")
                    st.write(f"**Sức khỏe:** {int(metrics.get('GenHlth', 0))}/5")
            
            st.markdown("<br>", unsafe_allow_html=True)