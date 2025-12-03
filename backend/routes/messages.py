from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.message_service import create_message, get_messages_by_assessment
from services.assessment_service import get_assessment_by_id
import google.generativeai as genai

bp = Blueprint('messages', __name__, url_prefix='/api')

def get_rag_content():
    """Get RAG knowledge files from Gemini File API"""
    file_ids_str = current_app.config.get('KNOWLEDGE_FILE_IDS', '')
    if not file_ids_str:
        current_app.logger.warning("No KNOWLEDGE_FILE_IDS configured")
        return []
    
    file_id_list = [fid.strip() for fid in file_ids_str.split(',') if fid.strip()]
    rag_files = []
    
    for file_id in file_id_list:
        try:
            file_obj = genai.get_file(file_id)
            rag_files.append(file_obj)
            current_app.logger.info(f"Loaded RAG file: {file_id}")
        except Exception as e:
            current_app.logger.error(f"Error loading RAG file {file_id}: {e}")
    
    return rag_files

def build_context_prompt(assessment: dict, chat_history: list) -> str:
    """Build context prompt with assessment info and chat history for AI memory"""
    metrics = assessment.get('metrics', {})
    prediction = assessment.get('prediction', {})
    
    risk_level = prediction.get('risk_level', 'unknown')
    prediction_value = prediction.get('prediction', 0)
    
    # Parse prediction
    pred_text = "⚠️ NGUY CƠ CAO (Có khả năng mắc tiểu đường)" if risk_level == 'high' or prediction_value == 1 else "✅ NGUY CƠ THẤP (An toàn)"
    
    # Extract risk factors
    risk_factors = []
    if metrics.get('HighBP') == 1.0:
        risk_factors.append("Cao huyết áp")
    if metrics.get('HighChol') == 1.0:
        risk_factors.append("Cholesterol cao")
    if metrics.get('BMI', 0) >= 25:
        risk_factors.append(f"BMI {metrics.get('BMI'):.1f} (Thừa cân/Béo phì)")
    if metrics.get('Smoker') == 1.0:
        risk_factors.append("Hút thuốc")
    if metrics.get('PhysActivity') == 0.0:
        risk_factors.append("Ít vận động")
    if metrics.get('HeartDiseaseorAttack') == 1.0:
        risk_factors.append("Tiền sử bệnh tim")
    if metrics.get('Stroke') == 1.0:
        risk_factors.append("Tiền sử đột quỵ")
    if metrics.get('DiffWalk') == 1.0:
        risk_factors.append("Khó khăn khi đi bộ")
    
    risk_text = ", ".join(risk_factors) if risk_factors else "Không có yếu tố rủi ro đáng kể"
    
    # Age mapping
    age_map = {
        1: "18-24", 2: "25-29", 3: "30-34", 4: "35-39", 5: "40-44",
        6: "45-49", 7: "50-54", 8: "55-59", 9: "60-64", 10: "65-69",
        11: "70-74", 12: "75-79", 13: "80+"
    }
    age_text = age_map.get(int(metrics.get('Age', 0)), "N/A")
    
    # Health status mapping
    health_map = {1: "Rất tốt", 2: "Tốt", 3: "Bình thường", 4: "Kém", 5: "Rất kém"}
    health_text = health_map.get(int(metrics.get('GenHlth', 3)), "Bình thường")
    
    # Build context
    context = f"""BẠN LÀ BÁC SĨ AI CHUYÊN VỀ TIỂU ĐƯỜNG VÀ SỨC KHỎE.

╔══════════════════════════════════════════════════════════════╗
║           THÔNG TIN HỒ SƠ SỨC KHỎE BỆNH NHÂN                ║
╚══════════════════════════════════════════════════════════════╝

📊 KẾT QUẢ ĐÁNH GIÁ: {pred_text}
   • Mức độ rủi ro: {risk_level.upper()}
   • Thời điểm đo: {assessment.get('measured_at', 'N/A')}
   • Trạng thái: {'✅ Hiệu lực' if assessment.get('is_valid') else '❌ Đã hết hiệu lực'}

👤 THÔNG TIN CƠ BẢN:
   • Giới tính: {'Nam' if metrics.get('Sex')==1.0 else 'Nữ'}
   • Nhóm tuổi: {age_text}
   • BMI: {metrics.get('BMI', 'N/A')}
   • Sức khỏe tổng quan: {health_text} ({metrics.get('GenHlth', 'N/A')}/5)

⚠️ CÁC YẾU TỐ RỦI RO:
   {risk_text}

💊 TÌNH TRẠNG SỨC KHỎE:
   • Số ngày không khỏe (thể chất): {int(metrics.get('PhysHlth', 0))} ngày/30 ngày
   • Số ngày không khỏe (tâm thần): {int(metrics.get('MentHlth', 0))} ngày/30 ngày
   • Khó khăn khi đi bộ: {'Có' if metrics.get('DiffWalk')==1.0 else 'Không'}
   • Có bảo hiểm y tế: {'Có' if metrics.get('AnyHealthcare')==1.0 else 'Không'}

╔══════════════════════════════════════════════════════════════╗
║              LỊCH SỬ TRÒ CHUYỆN GẦN ĐÂY                      ║
╚══════════════════════════════════════════════════════════════╝
"""
    
    # Add recent chat history (last 10 messages for context)
    if chat_history:
        for msg in chat_history[-10:]:
            role_display = "🧑 Bệnh nhân" if msg['sender_type'] == 'user' else "👨‍⚕️ Bác sĩ AI"
            context += f"\n{role_display}: {msg['content']}\n"
    else:
        context += "\n(Đây là lần đầu tiên trò chuyện với bệnh nhân này)\n"
    
    return context

@bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """Handle chat with AI - includes memory from assessment and chat history"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        assessment_id = data.get('assessment_id')
        
        if not assessment_id:
            return jsonify({"error": "assessment_id is required"}), 400
        
        # Get assessment
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({"error": "Assessment not found"}), 404
        
        user_id = get_jwt_identity()     
        
        owner_id = str(assessment.get("user_id"))
        if str(owner_id) != str(user_id):
            return jsonify({"error": "Forbidden: not your assessment"}), 403
        
        user_message = data.get('user_message')
        
        # Get chat history (for memory)
        chat_history = get_messages_by_assessment(assessment_id)
        
        # Build context with assessment info and chat history
        context = build_context_prompt(assessment, chat_history)
        
        # Generate AI response
        if user_message is None:
            # Initial advice (first message)
            prompt = f"""{context}

╔══════════════════════════════════════════════════════════════╗
║                    YÊU CẦU TƯ VẤN BAN ĐẦU                    ║
╚══════════════════════════════════════════════════════════════╝

Hãy đưa ra lời khuyên ban đầu cho bệnh nhân dựa trên hồ sơ sức khỏe trên.
Phản hồi của bạn cần bao gồm:

1. 💬 **Nhận xét về kết quả đánh giá**
   - Giải thích ý nghĩa của kết quả dự đoán
   - Đánh giá mức độ rủi ro

2. 🎯 **Phân tích các yếu tố rủi ro**
   - Chi tiết về từng yếu tố nguy hiểm
   - Tác động của chúng đến nguy cơ tiểu đường

3. ✅ **3-5 hành động cụ thể cần làm ngay**
   - Các bước thực tế và khả thi
   - Ưu tiên theo mức độ quan trọng

4. 🥗 **Khuyến nghị về chế độ ăn uống**
   - Thực phẩm nên ăn
   - Thực phẩm nên tránh

5. 🏃 **Khuyến nghị về vận động**
   - Loại hình vận động phù hợp
   - Tần suất và thời lượng

6. 🏥 **Lời khuyên về khám bác sĩ**
   - Khi nào cần đi khám
   - Các xét nghiệm cần làm

Hãy viết một cách cảm thông, dễ hiểu và khuyến khích!
Sử dụng tiếng Việt và emoji để dễ đọc.
"""
        else:
            # User asking question - save user message first
            user_msg_result = create_message(assessment_id, 'user', user_message)
            if not user_msg_result.get('success'):
                current_app.logger.error(f"Failed to save user message: {user_msg_result.get('error')}")
            # Rebuild context with new message
            context = build_context_prompt(assessment, chat_history)
            
            prompt = f"""{context}

╔══════════════════════════════════════════════════════════════╗
║                      CÂU HỎI MỚI NHẤT                        ║
╚══════════════════════════════════════════════════════════════╝

🧑 Bệnh nhân hỏi: {user_message}

╔══════════════════════════════════════════════════════════════╗
║                    HƯỚNG DẪN TRẢ LỜI                         ║
╚══════════════════════════════════════════════════════════════╝

Hãy trả lời câu hỏi dựa trên:

1. **Thông tin hồ sơ sức khỏe** của bệnh nhân (đã cung cấp ở trên)
2. **Lịch sử trò chuyện** trước đó để duy trì맥락 (context)
3. **Kiến thức y khoa** từ tài liệu đính kèm
4. **Kết quả đánh giá** nguy cơ tiểu đường

Yêu cầu:
✓ Trả lời ngắn gọn, dễ hiểu
✓ Thân thiện và cảm thông
✓ Cung cấp thông tin chính xác
✓ Đưa ra lời khuyên thực tế
✓ Liên hệ với tình trạng cụ thể của bệnh nhân
✓ Sử dụng tiếng Việt và emoji
"""
        
        # Call Gemini with RAG
        rag_files = get_rag_content()
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        content_to_send = [prompt] + rag_files
        response = model.generate_content(content_to_send)
        ai_response = response.text
        
        # Save AI message (sender_type = 'agent')
        create_message(assessment_id, 'agent', ai_response)
        
        current_app.logger.info(f"Chat response generated for assessment {assessment_id}")
        
        return jsonify({
            "response": ai_response,
            "message": "Response generated successfully"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/messages/assessment/<assessment_id>', methods=['GET'])
@jwt_required()
def get_messages(assessment_id):
    """Get chat history of an assessment"""
    try:
        user_id = get_jwt_identity()
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({"error": "Assessment not found"}), 404

        if str(assessment.get("user_id")) != str(user_id):
            return jsonify({"error": "Forbidden: not your assessment"}), 403
        
        messages = get_messages_by_assessment(assessment_id)
        return jsonify(messages), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/messages/assessment/<assessment_id>', methods=['DELETE'])
@jwt_required()
def delete_messages(assessment_id):
    """Delete all messages of an assessment"""
    try:
        from services.message_service import delete_messages_by_assessment
        user_id = get_jwt_identity()
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({"error": "Assessment not found"}), 404

        if str(assessment.get("user_id")) != str(user_id):
            return jsonify({"error": "Forbidden: not your assessment"}), 403
        
        count = delete_messages_by_assessment(assessment_id)
        return jsonify({
            "message": f"Deleted {count} messages",
            "deleted_count": count
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500