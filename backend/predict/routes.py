from flask import Blueprint, request, jsonify, current_app
from predict.validation import validate_health_form
from predict.predict_model import predictor
from services.assessment_service import create_assessment, get_assessment_by_id
from services.message_service import create_message
import google.generativeai as genai

bp = Blueprint('app_routes', __name__, url_prefix='/api')

def get_rag_content():
    """Lấy danh sách File Reference từ ID đã cấu hình"""
    file_ids_str = current_app.config.get('KNOWLEDGE_FILE_IDS')
    if not file_ids_str:
        current_app.logger.warning("KNOWLEDGE_FILE_IDS not configured")
        return []
    
    # Tách chuỗi ID thành list và lấy reference
    file_id_list = [fid.strip() for fid in file_ids_str.split(',') if fid.strip()]
    rag_files = []
    
    for fid in file_id_list:
        try:
            file_obj = genai.get_file(fid)
            rag_files.append(file_obj)
            current_app.logger.info(f"Loaded RAG file: {fid}")
        except Exception as e:
            current_app.logger.error(f"Error loading file {fid}: {e}")
    
    return rag_files

def generate_response_with_files(prompt_text):
    """Gọi Gemini với Prompt và Danh sách File"""
    try:
        rag_files = get_rag_content()
        if not rag_files:
            return "Hệ thống chưa tải được tài liệu kiến thức. Vui lòng kiểm tra cấu hình."

        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Gửi Prompt + Tất cả File
        content_to_send = [prompt_text] + rag_files
        response = model.generate_content(content_to_send)
        return response.text
    except Exception as e:
        current_app.logger.error(f"Gemini error: {e}")
        return "Xin lỗi, hệ thống đang bận. Vui lòng thử lại sau."
    
def build_profile_text(record):
    """Tạo tóm tắt hồ sơ người dùng để AI nhớ ngữ cảnh"""
    if not record:
        return "Chưa có hồ sơ sức khỏe."
    
    # Hỗ trợ cả format cũ và mới
    data = record.get('form_data') or record.get('metrics', {})
    pred_data = record.get('prediction', {})
    
    # Lấy prediction value
    if isinstance(pred_data, dict):
        pred = pred_data.get('prediction', 0)
        risk_level = pred_data.get('risk_level', 'unknown')
    else:
        pred = pred_data
        risk_level = 'high' if pred == 1 else 'low'
    
    # Logic dự đoán 0/1
    pred_text = "⚠️ Nguy cơ CAO (Có khả năng tiểu đường)" if pred == 1 else "✅ Nguy cơ THẤP (An toàn)"
    
    factors = []
    if data.get('HighBP') == 1.0:
        factors.append("Cao huyết áp")
    if data.get('HighChol') == 1.0:
        factors.append("Cholesterol cao")
    if data.get('BMI', 0) >= 25:
        factors.append(f"BMI {data.get('BMI'):.1f} (Thừa cân)")
    if data.get('Smoker') == 1.0:
        factors.append("Hút thuốc")
    if data.get('PhysActivity') == 0.0:
        factors.append("Ít vận động")
    if data.get('HeartDiseaseorAttack') == 1.0:
        factors.append("Tiền sử bệnh tim")
    if data.get('Stroke') == 1.0:
        factors.append("Tiền sử đột quỵ")
    
    risk_text = ", ".join(factors) if factors else "Không có yếu tố rủi ro đáng kể"
    
    # Age mapping
    age_map = {
        1: "18-24", 2: "25-29", 3: "30-34", 4: "35-39", 5: "40-44",
        6: "45-49", 7: "50-54", 8: "55-59", 9: "60-64", 10: "65-69",
        11: "70-74", 12: "75-79", 13: "80+"
    }
    age_text = age_map.get(int(data.get('Age', 0)), "N/A")
    
    return f"""
╔══════════════════════════════════════════════════════════════╗
║           THÔNG TIN HỒ SƠ SỨC KHỎE BỆNH NHÂN                ║
╚══════════════════════════════════════════════════════════════╝

📊 KẾT QUẢ ĐÁNH GIÁ: {pred_text}
   • Mức độ rủi ro: {risk_level.upper()}

👤 THÔNG TIN CƠ BẢN:
   • Giới tính: {'Nam' if data.get('Sex')==1.0 else 'Nữ'}
   • Nhóm tuổi: {age_text}
   • BMI: {data.get('BMI', 'N/A')}

⚠️ CÁC YẾU TỐ RỦI RO:
   {risk_text}

💊 TÌNH TRẠNG SỨC KHỎE:
   • Số ngày không khỏe (thể chất): {int(data.get('PhysHlth', 0))} ngày/30 ngày
   • Số ngày không khỏe (tâm thần): {int(data.get('MentHlth', 0))} ngày/30 ngày
"""

@bp.route('/analyze_risk', methods=['POST'])
def analyze_risk():
    """Bước 1: Validate + Predict (không lưu DB)"""
    try:
        form_data = request.get_json()
        
        # 1. Validate
        is_valid, result = validate_health_form(form_data)
        if not is_valid:
            return jsonify({"error": result}), 400
        
        validated_data = result

        # 2. Predict
        try:
            if predictor is None:
                raise RuntimeError("Predictor not initialized")
            
            prediction = predictor.predict(validated_data)
            
            # Get probabilities
            try:
                proba = predictor.predict_proba(validated_data)
                risk_score = proba.get('high_risk', float(prediction))
            except:
                risk_score = float(prediction)
            
            current_app.logger.info(f"Prediction: {prediction}, Risk score: {risk_score:.2%}")
            
        except Exception as e:
            current_app.logger.error(f"Model error: {e}")
            return jsonify({"error": f"Lỗi mô hình dự đoán: {str(e)}"}), 500

        # Trả về kết quả ngay lập tức
        return jsonify({
            "prediction": int(prediction),
            "risk_level": "high" if prediction == 1 else "low",
            "risk_score": risk_score,
            "validated_data": validated_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Analyze risk error: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/get_advice', methods=['POST'])
def get_advice():
    """Bước 2: Generate advice (có thể lưu DB nếu có user_id)"""
    try:
        data = request.get_json()
        validated_data = data.get('validated_data')
        prediction = data.get('prediction')
        user_id = data.get('user_id')  # Optional
        risk_score = data.get('risk_score', float(prediction))

        if validated_data is None or prediction is None:
            return jsonify({"error": "Thiếu dữ liệu đầu vào"}), 400

        # Build profile
        profile_txt = build_profile_text({
            'form_data': validated_data,
            'prediction': prediction
        })
        
        # Generate advice
        prompt = f"""
Bạn là bác sĩ tư vấn AI chuyên về bệnh tiểu đường.
Dựa CHÍNH XÁC vào các tài liệu đính kèm, hãy đưa ra lời khuyên ban đầu cho bệnh nhân này:

{profile_txt}

Yêu cầu phản hồi:
1. 💬 **Thông báo kết quả** một cách cảm thông và dễ hiểu
2. 🎯 **Giải thích ngắn gọn** về các yếu tố rủi ro liên quan
3. ✅ **3-5 hành động cụ thể** cần làm ngay (thực tế, khả thi)
4. 🥗 **Chế độ ăn uống** phù hợp (thực phẩm nên ăn/tránh)
5. 🏃 **Hoạt động thể chất** phù hợp (loại hình, tần suất, thời lượng)
6. 🏥 **Lời khuyên về khám bác sĩ** (khi nào, xét nghiệm gì)

Hãy viết bằng tiếng Việt, dễ hiểu, thân thiện và có emoji để dễ đọc!
"""
        
        advice = generate_response_with_files(prompt)

        # Optional: Save to DB if user_id provided
        assessment_id = None
        if user_id:
            try:
                # Save assessment
                assessment_id = create_assessment(
                    user_id=user_id,
                    form_data=validated_data,
                    prediction=int(prediction),
                    risk_score=risk_score
                )
                
                # Save advice as initial message
                create_message(
                    assessment_id=assessment_id,
                    sender_type='agent',
                    content=advice,
                    metadata={'type': 'initial_advice'}
                )
                
                current_app.logger.info(f"Saved assessment {assessment_id} for user {user_id}")
                
            except Exception as e:
                current_app.logger.error(f"Error saving to DB: {e}")
                # Continue anyway, advice is still valid

        # Return advice
        return jsonify({
            "advice": advice,
            "assessment_id": assessment_id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get advice error: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/chat_with_rag', methods=['POST'])
def chat_with_rag():
    """Chat với AI sử dụng RAG"""
    try:
        data = request.get_json()
        user_message = data.get('user_message')
        assessment_id = data.get('assessment_id')
        context = data.get('context', '')
        
        if not user_message:
            return jsonify({"error": "user_message is required"}), 400
        
        # Get assessment for context if provided
        if assessment_id:
            try:
                assessment = get_assessment_by_id(assessment_id)
                if assessment:
                    context = build_profile_text(assessment)
            except:
                pass
        
        # Build prompt
        prompt = f"""
Bạn là bác sĩ tư vấn AI chuyên về bệnh tiểu đường.

{context}

🧑 Bệnh nhân hỏi: {user_message}

Hãy trả lời dựa trên:
1. Kiến thức y khoa từ tài liệu đính kèm
2. Thông tin ngữ cảnh (nếu có)
3. Tính thực tế và dễ hiểu

Yêu cầu:
✓ Trả lời ngắn gọn, súc tích
✓ Thân thiện và cảm thông
✓ Cung cấp thông tin chính xác
✓ Đưa ra lời khuyên thực tế
✓ Sử dụng tiếng Việt và emoji
"""
        
        # Generate response
        response_text = generate_response_with_files(prompt)
        
        # Save to DB if assessment_id provided
        if assessment_id:
            try:
                # Save user message
                create_message(
                    assessment_id=assessment_id,
                    sender_type='user',
                    content=user_message
                )
                
                # Save AI response
                create_message(
                    assessment_id=assessment_id,
                    sender_type='agent',
                    content=response_text
                )
                
                current_app.logger.info(f"Saved chat to assessment {assessment_id}")
                
            except Exception as e:
                current_app.logger.error(f"Error saving chat: {e}")
        
        return jsonify({
            "response": response_text
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Chat with RAG error: {e}")
        return jsonify({"error": str(e)}), 500