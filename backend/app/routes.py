from flask import Blueprint, request, jsonify, current_app
from app.validation import validate_health_form
import requests
import google.generativeai as genai
import os

bp = Blueprint('routes', __name__)

def load_knowledge_base():
    """Tải file kiến thức RAG"""
    try:
        kb_path = os.path.join(os.path.dirname(__file__), 'knowledge.md')
        with open(kb_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        current_app.logger.error(f"Không thể tải knowledge.md: {e}")
        return "Lỗi: Không thể tải cơ sở tri thức."

def get_ai_agent_advice(prediction, user_data, knowledge_base):
    """
    Gọi Gemini API (RAG) để sinh lời khuyên (Chỉ 0 hoặc 1)
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # === THAY ĐỔI LOGIC: CHỈ CÓ 0 HOẶC 1 ===
    if prediction == 1:
        prediction_text = "1 (Có nguy cơ mắc Tiểu đường)"
    else:
        prediction_text = "0 (Không có nguy cơ)"

    # Tạo tóm tắt hồ sơ
    profile_summary = []
    if user_data['HighBP'] == 1: profile_summary.append("Bị cao huyết áp")
    if user_data['BMI'] >= 25: profile_summary.append(f"BMI {user_data['BMI']} (Thừa cân/Béo phì)")
    if user_data['Smoker'] == 1: profile_summary.append("Có hút thuốc")
    if user_data['PhysActivity'] == 0: profile_summary.append("Không hoạt động thể chất")
    if user_data['GenHlth'] >= 4: profile_summary.append("Sức khỏe chung Trung bình/Kém")
    
    profile_text = ", ".join(profile_summary) if profile_summary else "Không có yếu tố rủi ro nổi bật."

    prompt = f"""
    {knowledge_base}
    ---
    **YÊU CẦU:**
    Bạn là một trợ lý y tế AI. Dựa **TUYỆT ĐỐI** vào CƠ SỞ TRI THỨC Y TẾ bên trên:
    
    1.  Tìm kịch bản phù hợp (0 hoặc 1).
    2.  Trích xuất lời khuyên chung (bắt buộc) cho kịch bản đó.
    3.  Xem xét các yếu tố cá nhân hóa và chỉ chọn những lời khuyên cá nhân hóa có liên quan.
    4.  Trình bày lời khuyên một cách rõ ràng, "uy tín", và nhấn mạnh việc đi gặp bác sĩ nếu kết quả là 1.

    **Thông tin người dùng:**
    * **Kết quả dự đoán từ Model:** {prediction_text}
    * **Hồ sơ yếu tố rủi ro:** {profile_text}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        current_app.logger.error(f"Lỗi khi gọi Gemini API: {e}")
        return "Đã có lỗi xảy ra khi phân tích kết quả. Vui lòng thử lại."

@bp.route('/predict', methods=['POST'])
def predict_and_advise():
    # 1. Validate Form
    form_data = request.get_json()
    is_valid, result = validate_health_form(form_data)
    
    if not is_valid:
        return jsonify({"error": result}), 400
    
    validated_data = result

    # 2. Gọi Model Dự đoán (Giả lập)
    try:
        model_api_url = current_app.config['MOCK_MODEL_URL']
        model_response = requests.post(model_api_url, json=validated_data)
        model_response.raise_for_status()
        # === THAY ĐỔI LOGIC: Mong đợi 0 hoặc 1 ===
        prediction = model_response.json().get('prediction') 
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Không thể gọi Model dự đoán: {e}")
        return jsonify({"error": "Không thể kết nối đến máy chủ dự đoán."}), 503
    
    # Model phải trả về 0 (Không) hoặc 1 (Có)
    if prediction not in [0, 1]:
        return jsonify({"error": "Model dự đoán trả về kết quả không hợp lệ (phải là 0 hoặc 1)."}), 500

    # 3. Gọi AI Agent (Gemini RAG)
    knowledge_base = load_knowledge_base()
    advice = get_ai_agent_advice(prediction, validated_data, knowledge_base)

    # 4. Trả lời khuyên về Frontend
    return jsonify({"advice": advice}), 200