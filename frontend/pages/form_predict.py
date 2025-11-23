import streamlit as st
import requests
import time

# Cấu hình API backend
# Lưu ý: Đảm bảo server Flask của bạn đang chạy ở port 5000
# Nếu Flask không set prefix '/api', hãy đổi thành "http://127.0.0.1:5000"
BACKEND_URL = "http://127.0.0.1:5000/api"

# --- HÀM HỖ TRỢ MAPPING DỮ LIỆU ---
def map_user_input_to_api(inputs):
    # 1. Xử lý Tuổi
    age_map = {
        "18-24": 1, "25-29": 2, "30-34": 3, "35-39": 4, "40-44": 5,
        "45-49": 6, "50-54": 7, "55-59": 8, "60-64": 9, "65-69": 10,
        "70-74": 11, "75-79": 12, "80 trở lên": 13
    }
    
    # 2. Xử lý Học vấn
    edu_map = {
        "Chưa đi học": 1, "Tiểu học (Cấp 1)": 2, "THCS (Cấp 2)": 3,
        "THPT (Cấp 3)": 4, "Cao đẳng / Đại học (1-3 năm)": 5, "Đại học (4 năm trở lên)": 6
    }

    # 3. Gom dữ liệu trả về
    return {
        "HighBP": 1.0 if inputs['high_bp'] else 0.0,
        "HighChol": 1.0 if inputs['high_chol'] else 0.0,
        "CholCheck": 1.0 if inputs['chol_check'] else 0.0,
        "BMI": round(inputs['weight'] / ((inputs['height'] / 100) ** 2), 1),
        "Smoker": 1.0 if inputs['smoker'] else 0.0,
        "Stroke": 1.0 if inputs['stroke'] else 0.0,
        "HeartDiseaseorAttack": 1.0 if inputs['heart_disease'] else 0.0,
        "PhysActivity": 1.0 if inputs['phys_activity'] else 0.0,
        "HvyAlcoholConsump": 1.0 if inputs['hvy_alcohol'] else 0.0,
        "AnyHealthcare": 1.0 if inputs['healthcare'] else 0.0,
        "NoDocbcCost": 1.0 if inputs['no_doc_cost'] else 0.0,
        "GenHlth": float(inputs['gen_hlth']),     # Đã là số int từ slider
        "MentHlth": float(inputs['ment_hlth']),
        "PhysHlth": float(inputs['phys_hlth']),
        "DiffWalk": 1.0 if inputs['diff_walk'] else 0.0,
        "Sex": 1.0 if inputs['sex'] == "Nam" else 0.0,
        "Age": float(age_map[inputs['age_range']]),
        "Education": float(edu_map[inputs['education']]),
        "Income": float(inputs['income_index'])   # Đã là số int từ slider
    }

def local_css():
    st.markdown("""
    <style>
    .big-font {font-size:18px !important;}
    .stCheckbox label {font-size: 16px;}
    .prediction-card {
        padding: 20px; border-radius: 10px; text-align: center; margin-top: 20px; color: white;
    }
    .safe {background: linear-gradient(135deg, #56ab2f, #a8e063);}
    .danger {background: linear-gradient(135deg, #ff416c, #ff4b2b);}
    </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Trợ lý Sức khỏe AI", page_icon="🩺", layout="wide")
    local_css()

    st.title("🩺 Đánh giá Nguy cơ Tiểu đường")
    st.markdown("Hãy trả lời các câu hỏi dưới đây để AI phân tích hồ sơ sức khỏe của bạn.")

    with st.form("main_form"):
        # --- PHẦN 1: THÔNG TIN CƠ BẢN ---
        st.subheader("1. Thông tin Cá nhân")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sex = st.radio("Giới tính", ["Nam", "Nữ"], horizontal=True)
        with c2:
            age_range = st.selectbox("Nhóm tuổi", 
                ["18-24", "25-29", "30-34", "35-39", "40-44", "45-49", 
                 "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80 trở lên"], index=4)
        with c3:
            height = st.number_input("Chiều cao (cm)", 100, 250, 165)
        with c4:
            weight = st.number_input("Cân nặng (kg)", 30, 200, 60)
            
        # Hiển thị nhanh BMI
        bmi = weight / ((height/100)**2)
        if bmi < 18.5:
            st.info(f"BMI: {bmi:.1f} (Nhẹ cân)")
        elif 18.5 <= bmi < 23:
            st.success(f"BMI: {bmi:.1f} (Bình thường)")
        elif 23 <= bmi < 25:
            st.warning(f"BMI: {bmi:.1f} (Thừa cân)")
        else:
            st.error(f"BMI: {bmi:.1f} (Béo phì)")

        st.markdown("---")

        # --- PHẦN 2: TIỀN SỬ BỆNH (CHECKLIST) ---
        st.subheader("2. Tiền sử Y tế & Tình trạng")
        st.caption("Hãy đánh dấu vào những mục ĐÚNG với bạn (Bỏ qua nếu không có):")
        
        col_med1, col_med2 = st.columns(2)
        with col_med1:
            high_bp = st.checkbox("Từng bị Cao Huyết Áp")
            high_chol = st.checkbox("Từng được báo chỉ số Cholesterol (mỡ máu) cao")
            heart_disease = st.checkbox("Từng bị bệnh tim mạch hoặc nhồi máu cơ tim")
            stroke = st.checkbox("Từng bị đột quỵ")
            
        with col_med2:
            diff_walk = st.checkbox("Gặp khó khăn nghiêm trọng khi đi bộ hoặc leo thang")
            chol_check = st.checkbox("Đã kiểm tra mỡ máu trong 5 năm qua", value=True)
            healthcare = st.checkbox("Có bảo hiểm y tế", value=True)

        st.markdown("---")

        # --- PHẦN 3: LỐI SỐNG & CẢM NHẬN ---
        st.subheader("3. Thói quen & Sức khỏe chung")
        
        c_life1, c_life2 = st.columns(2)
        with c_life1:
            st.write("**Thói quen:**")
            smoker = st.toggle("Đã hút thuốc lá lâu năm? (> 100 điếu thuốc)")
            hvy_alcohol = st.toggle("Thường xuyên uống nhiều rượu bia?")
            phys_activity = st.toggle("Có tập thể dục/vận động trong 30 ngày qua?", value=True)
            no_doc_cost = st.toggle("Từng không đi khám bệnh vì vấn đề tài chính (trong 1 năm qua)?")
            
        with c_life2:
            st.write("**Tự đánh giá:**")
            
            # --- SỬA LỖI LOGIC: Dùng format_func ---
            # Dict map: Key là số (để gửi API), Value là text (để hiển thị)
            hlth_mapping = {
                1: "1 - Rất tốt", 
                2: "2 - Tốt", 
                3: "3 - Bình thường", 
                4: "4 - Kém", 
                5: "5 - Rất kém"
            }
            gen_hlth = st.select_slider(
                "Nhìn chung, sức khỏe bạn thế nào?",
                options=list(hlth_mapping.keys()), # List [1, 2, 3, 4, 5]
                format_func=lambda x: hlth_mapping[x], # Hiển thị Text
                value=2
            )
            
            phys_hlth = st.slider("Số ngày sức khỏe THỂ CHẤT không tốt (trong 30 ngày qua)", 0, 30, 0)
            ment_hlth = st.slider("Số ngày sức khỏe TÂM THẦN không tốt (lo âu, stress...)", 0, 30, 0)

        # --- PHẦN 4: KINH TẾ XÃ HỘI ---
        st.markdown("### 4. Yếu tố Kinh tế & Xã hội")
        st.caption("Các yếu tố này ảnh hưởng gián tiếp đến nguy cơ bệnh lý theo thống kê y tế.")
        
        c_soc1, c_soc2 = st.columns(2)
        
        with c_soc1:
            education = st.selectbox("Trình độ học vấn cao nhất", 
                ["Chưa đi học", "Tiểu học (Cấp 1)", "THCS (Cấp 2)", 
                 "THPT (Cấp 3)", "Cao đẳng / Đại học (1-3 năm)", "Đại học (4 năm trở lên)"], 
                index=3)
        
        with c_soc2:
            # --- SỬA LỖI LOGIC: Dùng format_func cho Income ---
            income_mapping = {
                1: "Mức 1 - Rất khó khăn", 2: "Mức 2 - Khó khăn", 3: "Mức 3 - Thấp",
                4: "Mức 4 - Cận trung bình", 5: "Mức 5 - Trung bình thấp", 6: "Mức 6 - Trung bình",
                7: "Mức 7 - Trung bình khá", 8: "Mức 8 - Khá", 9: "Mức 9 - Khá giả",
                10: "Mức 10 - Giàu có", 11: "Mức 11 - Thượng lưu"
            }
            
            income_index = st.select_slider(
                "Đánh giá mức sống / Điều kiện kinh tế hộ gia đình",
                options=list(income_mapping.keys()), # List [1...11]
                format_func=lambda x: income_mapping[x], # Hiển thị Text
                value=6
            )

        st.markdown("---")
        # Nút Submit nằm TRONG form
        submit = st.form_submit_button("🔍 PHÂN TÍCH NGAY", type="primary", use_container_width=True)

    # --- XỬ LÝ KẾT QUẢ (NẰM NGOÀI FORM) ---
    if submit:
        # Gom dữ liệu UI
        raw_data = {
            "sex": sex, "age_range": age_range, "height": height, "weight": weight,
            "high_bp": high_bp, "high_chol": high_chol, "chol_check": chol_check,
            "stroke": stroke, "heart_disease": heart_disease, "diff_walk": diff_walk,
            "healthcare": healthcare, "smoker": smoker, "hvy_alcohol": hvy_alcohol,
            "phys_activity": phys_activity, "no_doc_cost": no_doc_cost,
            "gen_hlth": gen_hlth,         # Lấy trực tiếp giá trị int (1-5)
            "phys_hlth": phys_hlth, "ment_hlth": ment_hlth,
            "education": education, 
            "income_index": income_index  # Lấy trực tiếp giá trị int (1-11)
        }
        
        # Map sang format model cần
        validated_data = map_user_input_to_api(raw_data)

        # 1. Gọi Model (Nhanh)
        prediction = None
        with st.status("Đang xử lý hồ sơ sức khỏe...", expanded=True) as status:
            time.sleep(0.5)
            st.write("🔍 Đang tính toán các chỉ số nguy cơ...")
            try:
                res = requests.post(f"{BACKEND_URL}/analyze_risk", json=validated_data)
                if res.status_code == 200:
                    data = res.json()
                    prediction = data['prediction']
                    server_validated = data['validated_data']
                    status.update(label="Đã hoàn tất phân tích!", state="complete", expanded=False)
                else:
                    status.update(label="Lỗi kết nối Server!", state="error")
                    st.error(f"Lỗi Server: {res.text}")
            except Exception as e:
                status.update(label="Không thể kết nối Server!", state="error")
                st.error(f"Lỗi kết nối: {e}")

        # 2. Hiển thị kết quả & Gọi AI (Nếu model chạy xong)
        if prediction is not None:
            # Layout kết quả
            c_res1, c_res2 = st.columns([1, 2])
            
            with c_res1:
                if prediction == 1:
                    st.markdown("""
                    <div class="prediction-card danger">
                        <h2>⚠️ NGUY CƠ CAO</h2>
                        <p>Mô hình dự đoán bạn có khả năng mắc tiểu đường.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="prediction-card safe">
                        <h2>✅ AN TOÀN</h2>
                        <p>Hiện tại các chỉ số cho thấy nguy cơ thấp.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with c_res2:
                st.subheader("💬 Bác sĩ AI tư vấn:")
                advice_box = st.empty()
                advice_box.info("Đang phân tích hồ sơ chi tiết để đưa ra lời khuyên...")
                
                # Gọi AI lấy lời khuyên
                try:
                    payload = {"validated_data": server_validated, "prediction": prediction}
                    adv_res = requests.post(f"{BACKEND_URL}/get_advice", json=payload)
                    if adv_res.status_code == 200:
                        advice = adv_res.json().get("advice")
                        advice_box.markdown(advice)
                    else:
                        advice_box.warning("Không thể tải lời khuyên chi tiết lúc này.")
                except:
                    advice_box.warning("Hệ thống AI đang bận, vui lòng thử lại sau.")

if __name__ == "__main__":
    main()