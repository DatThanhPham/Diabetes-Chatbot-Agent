"""
Assessment Form - Health metrics input
"""
import streamlit as st
from services.assessment_service import analyze_risk
from components.risk_result_dialog import show_risk_result_dialog
from utils.helpers import calculate_bmi, validate_bmi
from utils.session_state import set_assessment_result
import base64
import os

# Constants
AGE_RANGES = [
    (18, 24), (25, 29), (30, 34), (35, 39), (40, 44),
    (45, 49), (50, 54), (55, 59), (60, 64), (65, 69),
    (70, 74), (75, 79), (80, 120)
]

SEX_OPTIONS = ['Nam', 'Nữ']

EDUCATION_OPTIONS = [
    'Không tốt nghiệp phổ thông',
    'Tốt nghiệp tiểu học',
    'Tốt nghiệp THCS',
    'Tốt nghiệp THPT',
    'Cao đẳng/Đại học (chưa tốt nghiệp)',
    'Cao đẳng/Đại học (đã tốt nghiệp)'
]

INCOME_OPTIONS = [
    '< 10 triệu/năm', '10-15 triệu/năm', '15-20 triệu/năm',
    '20-25 triệu/năm', '25-35 triệu/năm', '35-50 triệu/năm',
    '50-75 triệu/năm', '> 75 triệu/năm'
]

GENHLTH_OPTIONS = ['Xuất sắc', 'Rất tốt', 'Khá tốt', 'Trung bình', 'Kém']

def get_base64_image(image_path):
    """Convert image to base64"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Không thể load ảnh: {e}")
        return None

def map_age_to_group(age):
    """Map age to group index (1-13)"""
    for idx, (min_age, max_age) in enumerate(AGE_RANGES, 1):
        if min_age <= age <= max_age:
            return idx
    return 1  # Default to first group

def show_assessment_form(user):
    """Display assessment form with improved UX"""
    
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
        background-color: rgba(255, 255, 255, 0.5);
        z-index: 0;
        pointer-events: none;
    }}
    
    .main > div {{
        position: relative;
        z-index: 1;
    }}
    
    /* Style form */
    .stForm {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }}
    
    /* Health option cards */
    .health-option {{
        background-color: white;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .health-option:hover {{
        border-color: #667eea;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }}
    
    .health-option.selected {{
        border-color: #667eea;
        background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
    }}
    </style>
    """ if base64_image else ""
    
    st.markdown(background_css, unsafe_allow_html=True)
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4; text-shadow: 2px 2px 4px rgba(255,255,255,0.8);">📝 Đánh Giá Sức Khỏe</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # ✅ Check if we have prediction result -> show dialog
    if 'prediction_result' in st.session_state:
        show_risk_result_dialog(st.session_state.prediction_result)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Đánh giá lại", key="new_assessment", use_container_width=True):
                del st.session_state.prediction_result
                if 'advice_requested' in st.session_state:
                    del st.session_state.advice_requested
                if 'show_streaming' in st.session_state:
                    del st.session_state.show_streaming
                st.rerun()
        
        return
    
    # ✅ Original form
    st.info("📋 Vui lòng điền đầy đủ thông tin sức khỏe của bạn")
    
    with st.form("health_assessment_form"):
        st.markdown("### 👤 Thông tin cơ bản")
        col1, col2 = st.columns(2)
        
        with col1:
            age_input = st.number_input("🎂 Tuổi", min_value=18, max_value=120, step=1)
            age_group = map_age_to_group(age_input)
            
            sex = st.selectbox("⚧️ Giới tính", options=SEX_OPTIONS, index=0)
        
        with col2:
            education = st.selectbox("🎓 Học vấn", options=EDUCATION_OPTIONS, index=3)
            income = st.selectbox("💰 Thu nhập", options=INCOME_OPTIONS, index=4)
        
        st.markdown("---")
        st.markdown("### 📏 Chỉ số cơ thể")
        
        col1, col2 = st.columns(2)
        
        with col1:
            height_cm = st.number_input("📐 Chiều cao (cm)", min_value=100, max_value=250, value=170, step=1)
        
        with col2:
            weight_kg = st.number_input("⚖️ Cân nặng (kg)", min_value=30, max_value=200, value=70, step=1)
        
        bmi = calculate_bmi(weight_kg, height_cm)
        is_valid_bmi, bmi_message = validate_bmi(bmi)
        
        if is_valid_bmi:
            st.success(f"✅ BMI: {bmi:.1f}")
        else:
            st.error(f"❌ {bmi_message}")
        
        st.markdown("---")
        st.markdown("### 🏥 Tình trạng sức khỏe")
        
        col1, col2 = st.columns(2)
        
        with col1:
            high_bp = st.checkbox("🩺 Huyết áp cao")
            high_chol = st.checkbox("💊 Cholesterol cao")
            chol_check = st.checkbox("🔬 Đã kiểm tra cholesterol (5 năm gần đây)")
            smoker = st.checkbox("🚬 Hút thuốc")
            stroke = st.checkbox("🧠 Tiền sử đột quỵ")
        
        with col2:
            heart_disease = st.checkbox("❤️ Bệnh tim mạch")
            phys_activity = st.checkbox("🏃 Hoạt động thể chất đều đặn")
            hvy_alcohol = st.checkbox("🍺 Uống nhiều rượu")
            any_healthcare = st.checkbox("🏥 Có bảo hiểm y tế")
            no_doc_cost = st.checkbox("💸 Không đủ tiền khám bệnh")
        
        st.markdown("---")
        st.markdown("### 🍎 Sức khỏe tổng quát")
        
        # General Health - Radio buttons instead of slider
        st.markdown("**💪 Sức khỏe chung**")
        gen_hlth = st.radio(
            "Đánh giá sức khỏe tổng quát của bạn:",
            options=GENHLTH_OPTIONS,
            horizontal=True,
            index=2,
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            ment_hlth = st.number_input(
                "🧠 Số ngày sức khỏe tâm thần không tốt (30 ngày)",
                min_value=0,
                max_value=30,
                value=0,
                step=1
            )
        
        with col2:
            phys_hlth = st.number_input(
                "🤕 Số ngày sức khỏe thể chất không tốt (30 ngày)",
                min_value=0,
                max_value=30,
                value=0,
                step=1
            )
        
        diff_walk = st.checkbox("🚶 Khó khăn khi đi bộ hoặc leo cầu thang")
        
        submitted = st.form_submit_button("🔍 Phân tích nguy cơ", type="primary", use_container_width=True)
        
        if submitted:
            if not is_valid_bmi:
                st.error("❌ Vui lòng nhập chiều cao và cân nặng hợp lệ!")
                return
            
            # Prepare data
            form_data = {
                'HighBP': 1.0 if high_bp else 0.0,
                'HighChol': 1.0 if high_chol else 0.0,
                'CholCheck': 1.0 if chol_check else 0.0,
                'BMI': bmi,
                'Smoker': 1.0 if smoker else 0.0,
                'Stroke': 1.0 if stroke else 0.0,
                'HeartDiseaseorAttack': 1.0 if heart_disease else 0.0,
                'PhysActivity': 1.0 if phys_activity else 0.0,
                'HvyAlcoholConsump': 1.0 if hvy_alcohol else 0.0,
                'AnyHealthcare': 1.0 if any_healthcare else 0.0,
                'NoDocbcCost': 1.0 if no_doc_cost else 0.0,
                'GenHlth': float(GENHLTH_OPTIONS.index(gen_hlth) + 1),
                'MentHlth': float(ment_hlth),
                'PhysHlth': float(phys_hlth),
                'DiffWalk': 1.0 if diff_walk else 0.0,
                'Sex': 1.0 if sex == "Nam" else 0.0,
                'Age': float(age_group),
                'Education': float(EDUCATION_OPTIONS.index(education) + 1),
                'Income': float(INCOME_OPTIONS.index(income) + 1)
            }
            
            # Analyze risk
            with st.spinner("🔄 Đang phân tích..."):
                result = analyze_risk(form_data)
            
            if result['success']:
                st.session_state.prediction_result = result['data']
                st.rerun()
            else:
                st.error(f"❌ Lỗi: {result['error']}")