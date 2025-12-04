import time
from flask import Blueprint, request, jsonify, current_app
from predict.validation import validate_health_form
from predict.predict_model import predictor
from services.assessment_service import create_assessment, get_assessment_by_id
from services.message_service import create_message
import google.generativeai as genai
import traceback 

bp = Blueprint('app_routes', __name__, url_prefix='/api')

_rag_cache = {
    'files': None,
    'timestamp': None,
    'ttl': 3600  # Cache 1 hour
}

def get_rag_content():
    """Lấy danh sách File Reference từ ID đã cấu hình (cached with TTL)"""
    now = time.time()
    
    # Check if cache is valid
    if (_rag_cache['files'] is not None and 
        _rag_cache['timestamp'] is not None and 
        now - _rag_cache['timestamp'] < _rag_cache['ttl']):
        current_app.logger.info("Using cached RAG files")
        return _rag_cache['files']
    
    # Load fresh files
    file_ids_str = current_app.config.get('KNOWLEDGE_FILE_IDS')
    if not file_ids_str:
        current_app.logger.warning("KNOWLEDGE_FILE_IDS not configured")
        return tuple()
    
    file_id_list = [fid.strip() for fid in file_ids_str.split(',') if fid.strip()]
    rag_files = []
    
    for fid in file_id_list:
        try:
            file_obj = genai.get_file(fid)
            rag_files.append(file_obj)
            current_app.logger.info(f"Loaded RAG file: {fid}")
        except Exception as e:
            current_app.logger.error(f"Error loading file {fid}: {e}")
    
    # Update cache
    _rag_cache['files'] = tuple(rag_files)
    _rag_cache['timestamp'] = now
    current_app.logger.info(f"Cached {len(rag_files)} RAG files")
    
    return _rag_cache['files']

def generate_response_with_files(prompt_text):
    """Gọi Gemini với Prompt và Danh sách File"""
    try:
        rag_files = get_rag_content()
        if not rag_files:
            return "Hệ thống chưa tải được tài liệu kiến thức. Vui lòng kiểm tra cấu hình."

        model = genai.GenerativeModel('gemini-2.0-flash')
        content_to_send = [prompt_text] + list(rag_files)
        response = model.generate_content(content_to_send)
        return response.text
    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f"Gemini error: {e}")
        
        if '429' in error_msg or 'Resource exhausted' in error_msg:
            current_app.logger.warning(f"Rate limit hit: {e}")
            return """
⏳ **Hệ thống đang bận, vui lòng thử lại sau ít phút.**

Nguyên nhân: Đã vượt quá giới hạn số lượng yêu cầu.

Trong lúc chờ, bạn có thể:
• Xem lại kết quả đánh giá của mình
• Đọc các lời khuyên đã được lưu trước đó
• Thử lại sau 2-3 phút

"""
        
        return "Xin lỗi, hệ thống đang bận. Vui lòng thử lại sau."

def build_profile_text(record):
    """Tạo tóm tắt hồ sơ người dùng để AI nhớ ngữ cảnh"""
    if not record:
        return "Chưa có hồ sơ sức khỏe."
    
    data = record.get('form_data') or record.get('metrics', {})
    pred_data = record.get('prediction', {})
    
    if isinstance(pred_data, dict):
        pred = pred_data.get('prediction', 0)
        risk_level = pred_data.get('risk_level', 'unknown')
    else:
        pred = pred_data
        risk_level = 'high' if pred == 1 else 'low'
    
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
    
    age_map = {
        1: "18-24", 2: "25-29", 3: "30-34", 4: "35-39", 5: "40-44",
        6: "45-49", 7: "50-54", 8: "55-59", 9: "60-64", 10: "65-69",
        11: "70-74", 12: "75-79", 13: "80+"
    }
    age_text = age_map.get(int(data.get('Age', 0)), "N/A")
    
    return f"""
HỒ SƠ: {pred_text} ({risk_level})
Tuổi: {age_text} | Giới: {'Nam' if data.get('Sex')==1.0 else 'Nữ'} | BMI: {data.get('BMI', 'N/A')}
Rủi ro: {risk_text}
SứcKhỏe: ThểChất {int(data.get('PhysHlth', 0))}/30 ngày, TâmThần {int(data.get('MentHlth', 0))}/30 ngày
"""

@bp.route('/analyze_risk', methods=['POST'])
def analyze_risk():
    """Bước 1: Validate + Predict (không lưu DB)"""
    try:
        form_data = request.get_json()
        
        is_valid, result = validate_health_form(form_data)
        if not is_valid:
            return jsonify({"error": result}), 400
        
        validated_data = result

        try:
            if predictor is None:
                raise RuntimeError("Predictor not initialized")
            
            prediction = predictor.predict(validated_data)
            
            try:
                proba = predictor.predict_proba(validated_data)
                risk_score = proba.get('high_risk', float(prediction))
            except:
                risk_score = float(prediction)
            
            current_app.logger.info(f"Prediction: {prediction}, Risk score: {risk_score:.2%}")
            
        except Exception as e:
            current_app.logger.error(f"Model error: {e}")
            return jsonify({"error": f"Lỗi mô hình dự đoán: {str(e)}"}), 500

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
        user_id = data.get('user_id')
        risk_score = data.get('risk_score', float(prediction))

        current_app.logger.info(f"📥 get_advice called: user_id={user_id}, prediction={prediction}")

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
1. **Thông báo kết quả** một cách cảm thông và dễ hiểu
2. **Giải thích ngắn gọn** về các yếu tố rủi ro liên quan
3. **3-5 hành động cụ thể** cần làm ngay (thực tế, khả thi)
4. **Chế độ ăn uống** phù hợp (thực phẩm nên ăn/tránh)
5. **Hoạt động thể chất** phù hợp (loại hình, tần suất, thời lượng)
6. **Lời khuyên về khám bác sĩ** (khi nào, xét nghiệm gì)

Hãy viết bằng tiếng Việt, dễ hiểu, thân thiện và có emoji để dễ đọc!
"""
        
        current_app.logger.info("🤖 Generating advice with Gemini...")
        advice = generate_response_with_files(prompt)
        current_app.logger.info(f"✅ Advice generated: {len(advice)} chars")

        assessment_id = None
        if user_id:
            try:
                risk_level = 'high' if prediction == 1 else 'low'
                
                current_app.logger.info(f"💾 Creating assessment for user {user_id}...")
                
                result = create_assessment(
                    user_id=user_id,
                    metrics=validated_data,
                    prediction={
                        'prediction': int(prediction),
                        'risk_score': float(risk_score),
                        'risk_level': risk_level,
                        'model_version': 'stacking_ensemble_v1'
                    }
                )
                
                current_app.logger.info(f"📝 create_assessment result: {result}")
                
                if result.get('success'):
                    assessment_id = result['data']['id']
                    current_app.logger.info(f"✅ Assessment created: {assessment_id}")
                    
                    msg_result = create_message(
                        assessment_id=assessment_id,
                        sender_type='agent',
                        content=advice,
                        metadata={'type': 'initial_advice'}
                    )
                    
                    current_app.logger.info(f"📨 create_message result: {msg_result}")
                    
                    if msg_result.get('success'):
                        current_app.logger.info(f"✅ Initial advice saved as message")
                    else:
                        current_app.logger.warning(f"⚠️ Failed to save message: {msg_result.get('error')}")
                else:
                    current_app.logger.error(f"❌ Failed to create assessment: {result.get('error')}")
                
            except Exception as e:
                current_app.logger.error(f"❌ Error saving to DB: {e}")
                current_app.logger.error(traceback.format_exc())
                # Continue anyway - advice is still valid

        current_app.logger.info(f"📤 Returning advice: assessment_id={assessment_id}")
        
        return jsonify({
            "advice": advice,
            "assessment_id": assessment_id,
            "prediction": int(prediction),
            "risk_score": float(risk_score),
            "risk_level": "high" if prediction == 1 else "low"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"❌ Get advice error: {e}")
        current_app.logger.error(traceback.format_exc())
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
                    context = build_profile_text({
                        'metrics': assessment.get('metrics', {}),
                        'prediction': assessment.get('prediction', {})
                    })
            except Exception as e:
                current_app.logger.warning(f"Could not load assessment context: {e}")
        
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
                create_message(assessment_id, 'user', user_message)
                # Save AI response
                create_message(assessment_id, 'agent', response_text)
            except Exception as e:
                current_app.logger.warning(f"Could not save messages: {e}")
        
        return jsonify({
            "response": response_text
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Chat with RAG error: {e}")
        return jsonify({"error": str(e)}), 500