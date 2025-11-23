from flask import Blueprint, request, jsonify, current_app
from app.validation import validate_health_form
import requests
import google.generativeai as genai
import os

bp = Blueprint('routes', __name__)

def get_rag_content():
    """Lấy danh sách File Reference từ ID đã cấu hình"""
    file_ids_str = current_app.config.get('KNOWLEDGE_FILE_IDS')
    if not file_ids_str:
        return []
    
    # Tách chuỗi ID thành list và lấy reference
    file_id_list = [fid.strip() for fid in file_ids_str.split(',') if fid.strip()]
    try:
        return [genai.get_file(fid) for fid in file_id_list]
    except Exception as e:
        current_app.logger.error(f"Lỗi lấy file từ Google: {e}")
        return []

def generate_response_with_files(prompt_text):
    """Gọi Gemini với Prompt và Danh sách File"""
    try:
        rag_files = get_rag_content()
        if not rag_files:
            return "Hệ thống chưa tải được tài liệu kiến thức. Vui lòng kiểm tra cấu hình."

        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Gửi Prompt + Tất cả File
        content_to_send = [prompt_text] + rag_files
        response = model.generate_content(content_to_send)
        return response.text
    except Exception as e:
        current_app.logger.error(f"Lỗi Gemini: {e}")
        return "Xin lỗi, hệ thống đang bận. Vui lòng thử lại sau."
    
def build_profile_text(record):
    """Tạo tóm tắt hồ sơ người dùng để AI nhớ ngữ cảnh"""
    if not record: return "Chưa có hồ sơ sức khỏe."
    
    data = record.get('form_data', {})
    pred = record.get('prediction')
    
    # Logic dự đoán 0/1
    pred_text = "Nguy cơ CAO (Có khả năng tiểu đường)" if pred == 1 else "Nguy cơ THẤP (An toàn)"
    
    factors = []
    if data.get('HighBP') == 1: factors.append("Cao huyết áp")
    if data.get('BMI', 0) >= 25: factors.append(f"BMI {data['BMI']} (Thừa cân)")
    if data.get('Smoker') == 1: factors.append("Hút thuốc")
    if data.get('PhysActivity') == 0: factors.append("Lười vận động")
    
    risk_text = ", ".join(factors) if factors else "Không có yếu tố rủi ro lớn"
    
    return f"""
    - Tình trạng dự đoán: {pred_text}
    - Các yếu tố rủi ro chính: {risk_text}
    - Nhóm tuổi: {data.get('Age')}
    - Giới tính: {'Nam' if data.get('Sex')==1 else 'Nữ'}
    """


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
    profile_txt = build_profile_text({'form_data': validated_data, 'prediction': prediction})
    
    prompt = f"""
    Bạn là bác sĩ tư vấn AI chuyên về bệnh tiểu đường.
    Dựa CHÍNH XÁC vào các tài liệu đính kèm, hãy đưa ra lời khuyên ban đầu cho bệnh nhân này:
    {profile_txt}
    
    Yêu cầu:
    1. Thông báo kết quả dự đoán một cách cảm thông.
    2. Giải thích ngắn gọn về các yếu tố rủi ro liên quan.
    3. Đưa ra 3 hành động cụ thể cần làm ngay (dựa trên tài liệu).
    4. Gợi ý cách hoạt động thể chất và chế độ ăn uống phù hợp.
    5. Nhấn mạnh việc đi khám bác sĩ nếu nguy cơ cao.
    """
    advice = generate_response_with_files(prompt)

    # 4. Trả lời khuyên về Frontend
    return jsonify({"advice": advice}), 200