import streamlit as st
import requests
import json

# Cấu hình API backend
BACKEND_URL = "http://127.0.0.1:5000/api"

def display_health_form():
    st.title("Form Dự đoán Nguy cơ Tiểu đường 🤖")
    st.write("Vui lòng cung cấp các chỉ số sức khỏe của bạn một cách chính xác.")
    
    # Các lựa chọn cho form
    yes_no_map = {"Có": 1.0, "Không": 0.0}
    sex_map = {"Nam": 1.0, "Nữ": 0.0}
    age_map = {
        "18-24": 1.0, "25-29": 2.0, "30-34": 3.0, "35-39": 4.0, "40-44": 5.0,
        "45-49": 6.0, "50-54": 7.0, "55-59": 8.0, "60-64": 9.0, "65-69": 10.0,
        "70-74": 11.0, "75-79": 12.0, "80+": 13.0
    }
    gen_hlth_map = {"Rất tốt": 1.0, "Tốt": 2.0, "Trung bình": 3.0, "Kém": 4.0, "Rất kém": 5.0}
    edu_map = {
        "Chưa đi học": 1.0, "Tiểu học": 2.0, "THCS": 3.0,
        "THPT": 4.0, "Cao đẳng/Đại học 1-3 năm": 5.0, "Đại học 4+ năm": 6.0
    }
    income_map = {
        "<$15,000": 1.0, "$15,000 - $24,999": 2.0, "$25,000 - $34,999": 3.0,
        "$35,000 - $49,999": 4.0, "$50,000 - $74,999": 5.0, "$75,000 - $99,999": 6.0,
        "$100,000 - $149,999": 7.0, "$150,000 - $199,999": 8.0, "$200,000 - $249,999": 9.0,
        "$250,000 - $349,999": 10.0, "≥$350,000": 11.0
    }

    with st.form("health_form"):
        st.markdown("---")
        st.markdown("### I. Chỉ số Sức khỏe Chung")
        col1, col2 = st.columns(2)
        with col1:
            high_bp = st.radio("Bạn có bị cao huyết áp không?", ("Không", "Có"), horizontal=True)
            high_chol = st.radio("Cholesterol của bạn có cao không?", ("Không", "Có"), horizontal=True)
            chol_check = st.radio("Bạn có kiểm tra Cholesterol trong 5 năm qua?", ("Có", "Không"), horizontal=True)
            bmi = st.number_input("Chỉ số BMI của bạn (ví dụ: 22.5)", min_value=12.0, max_value=99.0, value=25.0, step=0.1)
        with col2:
            smoker = st.radio("Bạn có hút ít nhất 100 điếu thuốc trong đời?", ("Không", "Có"), horizontal=True)
            stroke = st.radio("Bạn đã từng bị đột quỵ?", ("Không", "Có"), horizontal=True)
            heart_disease = st.radio("Bạn có bị bệnh tim mạch vành hoặc nhồi máu cơ tim?", ("Không", "Có"), horizontal=True)

        st.markdown("---")
        st.markdown("### II. Lối sống")
        col3, col4 = st.columns(2)
        with col3:
            phys_activity = st.radio("Bạn có vận động thể chất (ngoài công việc) trong 30 ngày qua?", ("Có", "Không"), horizontal=True)
            hvy_alcohol = st.radio("Bạn có phải là người uống nhiều rượu bia (Nam >14, Nữ >7 ly/tuần)?", ("Không", "Có"), horizontal=True)
        with col4:
            gen_hlth = st.select_slider("Sức khỏe chung của bạn?", options=gen_hlth_map.keys())
            
        st.markdown("---")
        st.markdown("### III. Sức khỏe Thể chất & Tinh thần")
        col5, col6 = st.columns(2)
        with col5:
            phys_hlth = st.number_input("Trong 30 ngày qua, có bao nhiêu ngày sức khỏe thể chất bạn KHÔNG tốt?", min_value=0, max_value=30, value=0, step=1)
            ment_hlth = st.number_input("Trong 30 ngày qua, có bao nhiêu ngày sức khỏe tinh thần bạn KHÔNG tốt?", min_value=0, max_value=30, value=0, step=1)
        with col6:
            diff_walk = st.radio("Bạn có gặp khó khăn nghiêm trọng khi đi bộ/leo cầu thang?", ("Không", "Có"), horizontal=True)

        st.markdown("---")
        st.markdown("### IV. Thông tin Y tế & Xã hội")
        col7, col8 = st.columns(2)
        with col7:
            any_healthcare = st.radio("Bạn có bất kỳ loại hình bảo hiểm y tế nào không?", ("Có", "Không"), horizontal=True)
            no_doc_cost = st.radio("Trong 12 tháng qua, có lúc nào bạn không thể đi khám bác sĩ vì chi phí?", ("Không", "Có"), horizontal=True)
        with col8:
            sex = st.radio("Giới tính của bạn?", ("Nữ", "Nam"), horizontal=True)
            age = st.select_slider("Nhóm tuổi của bạn?", options=age_map.keys())

        st.markdown("---")
        st.markdown("### V. Học vấn & Thu nhập")
        col9, col10 = st.columns(2)
        with col9:
            education = st.select_slider("Trình độ học vấn cao nhất?", options=edu_map.keys())
        with col10:
            income = st.select_slider("Tổng thu nhập hộ gia đình hàng năm?", options=income_map.keys())
        
        submitted = st.form_submit_button("Gửi thông tin và Nhận tư vấn", type="primary", use_container_width=True)

        if submitted:
            # Map dữ liệu từ form về dạng số mà model cần
            data = {
                "HighBP": yes_no_map[high_bp],
                "HighChol": yes_no_map[high_chol],
                "CholCheck": yes_no_map[chol_check],
                "BMI": bmi,
                "Smoker": yes_no_map[smoker],
                "Stroke": yes_no_map[stroke],
                "HeartDiseaseorAttack": yes_no_map[heart_disease],
                "PhysActivity": yes_no_map[phys_activity],
                "HvyAlcoholConsump": yes_no_map[hvy_alcohol],
                "AnyHealthcare": yes_no_map[any_healthcare],
                "NoDocbcCost": yes_no_map[no_doc_cost],
                "GenHlth": gen_hlth_map[gen_hlth],
                "MentHlth": float(ment_hlth),
                "PhysHlth": float(phys_hlth),
                "DiffWalk": yes_no_map[diff_walk],
                "Sex": sex_map[sex],
                "Age": age_map[age],
                "Education": edu_map[education],
                "Income": income_map[income]
            }
                        
            with st.spinner("Đang xử lý... AI Agent đang phân tích hồ sơ của bạn..."):
                try:
                    response = requests.post(f"{BACKEND_URL}/predict", json=data)
                    if response.status_code == 200:
                        st.success("Đã nhận được lời khuyên từ AI Agent:")
                        st.markdown(response.json()['advice'])
                        st.balloons()
                    elif response.status_code == 400:
                        st.error(f"Lỗi nhập liệu: {response.json()['error']}")
                    else:
                        st.error(f"Lỗi máy chủ: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Không thể kết nối đến máy chủ backend.")
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi: {e}")

def main():
    # Kiểm tra login trước khi cho dự đoán
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Vui lòng đăng nhập để sử dụng chức năng này.")
        st.stop()

    display_health_form()

if __name__ == "__main__":
    main()