from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.message_service import create_message, get_messages_by_assessment, delete_messages_by_assessment
from services.assessment_service import get_assessment_by_id, get_assessments_by_user
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import time
import hashlib
import json  
import os   

bp = Blueprint('messages', __name__, url_prefix='/api')

# Cache settings cho response
_response_cache = {}
_response_cache_ttl = 300  
_response_cache_max_size = 100

_cache_stats = {
    'hits': 0,
    'misses': 0,
    'total_calls': 0
}

_rate_limiter = {}
MIN_REQUEST_INTERVAL = 2

def get_cache_key(prompt_text):
    return hashlib.md5(prompt_text.encode('utf-8')).hexdigest()

def get_cached_response(prompt_text):
    _cache_stats['total_calls'] += 1
    cache_key = get_cache_key(prompt_text)
    if cache_key in _response_cache:
        cached = _response_cache[cache_key]
        if time.time() - cached['timestamp'] < _response_cache_ttl:
            return cached['response']
        else:
            del _response_cache[cache_key]
    return None

def cache_response(prompt_text, response_text):
    if len(_response_cache) >= _response_cache_max_size:
        oldest_key = min(_response_cache.keys(), key=lambda k: _response_cache[k]['timestamp'])
        del _response_cache[oldest_key]
    cache_key = get_cache_key(prompt_text)
    _response_cache[cache_key] = {'response': response_text, 'timestamp': time.time()}

def check_rate_limit(user_id):
    if not user_id: return
    now = time.time()
    if user_id in _rate_limiter:
        if now - _rate_limiter[user_id] < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - (now - _rate_limiter[user_id]))
    _rate_limiter[user_id] = time.time()

def get_active_cache_name():
    """Đọc tên cache từ file JSON do script start_cache.py tạo ra"""
    if os.path.exists("cache_state.json"):
        try:
            with open("cache_state.json", "r") as f:
                data = json.load(f)
                return data.get("cache_name")
        except Exception as e:
            current_app.logger.error(f"Error reading cache state: {e}")
            return None
    return None

def build_profile_compact(record):
    if not record: return ""
    data = record.get('metrics', {})
    pred_data = record.get('prediction', {})
    if isinstance(pred_data, dict):
        pred = pred_data.get('prediction', 0)
        risk = pred_data.get('risk_level', 'low')
    else:
        pred = pred_data
        risk = 'high' if pred == 1 else 'low'
    
    factors = []
    if data.get('HighBP') == 1.0: factors.append("HA")
    if data.get('HighChol') == 1.0: factors.append("Chol")
    if data.get('BMI', 0) >= 25: factors.append(f"BMI{data.get('BMI'):.0f}")
    if data.get('Smoker') == 1.0: factors.append("Smoke")
    if data.get('PhysActivity') == 0.0: factors.append("NoEx")
    if data.get('HeartDiseaseorAttack') == 1.0: factors.append("Heart")
    if data.get('Stroke') == 1.0: factors.append("Stroke")
    
    age_map = {1:"18-24",2:"25-29",3:"30-34",4:"35-39",5:"40-44",6:"45-49",7:"50-54",8:"55-59",9:"60-64",10:"65-69",11:"70-74",12:"75-79",13:"80+"}
    age = age_map.get(int(data.get('Age', 0)), "N/A")
    sex = "M" if data.get('Sex')==1.0 else "F"
    bmi = data.get('BMI', 0)
    risk_icon = "⚠️" if pred == 1 else "✅"
    factors_str = ",".join(factors) if factors else "OK"
    return f"{risk_icon}{age}|{sex}|{bmi:.1f}|{risk}|{factors_str}"

def build_history_compact(assessments, limit=3):
    if not assessments: return ""
    recent = sorted(assessments, key=lambda x: x.get('measured_at', ''), reverse=True)[:limit]
    lines = []
    for idx, a in enumerate(recent, 1):
        profile = build_profile_compact(a)
        date = str(a.get('measured_at', ''))[:10]
        lines.append(f"{idx}.{date}:{profile}")
    return "\n".join(lines)

def build_chat_history_context(messages, limit=10):
    if not messages: return ""
    recent_messages = messages[-limit:] if len(messages) > limit else messages
    lines = []
    for msg in recent_messages:
        sender = msg.get('sender_type', 'unknown')
        content = msg.get('content', '')
        if sender == 'user':
            lines.append(f"User: {content}")
        else:
            lines.append(f"AI: {content}")
    return "\n".join(lines)

@bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    try:
        data = request.get_json()
        if not data: return jsonify({"error": "No data provided"}), 400
        
        assessment_id = data.get('assessment_id')
        user_message = data.get('user_message')
        
        if not assessment_id: return jsonify({"error": "assessment_id is required"}), 400
        
        # Get assessment & Check ownership
        assessment = get_assessment_by_id(assessment_id)
        if not assessment: return jsonify({"error": "Assessment not found"}), 404
        
        user_id = get_jwt_identity()
        if str(assessment.get("user_id")) != str(user_id): return jsonify({"error": "Forbidden"}), 403
        
        # Rate limiting
        check_rate_limit(user_id)
        
        context_lines = []
        profile = build_profile_compact(assessment)
        context_lines.append(f"Đánh giá hiện tại:{profile}")
        
        try:
            assessments = get_assessments_by_user(user_id, valid_only=False)
            if len(assessments) > 1:
                history = build_history_compact(assessments, limit=3)
                if history: context_lines.append(f"Lịch sử 3 lần đánh giá:\n{history}")
        except Exception: pass
        
        try:
            chat_messages = get_messages_by_assessment(assessment_id)
            if chat_messages:
                chat_history = build_chat_history_context(chat_messages, limit=10)
                if chat_history: context_lines.append(f"Lịch sử chat hiện tại:\n{chat_history}")
        except Exception: pass
        
        context = "\n\n".join(context_lines)
        
        # Generate prompt
        if user_message is None:
            prompt = f"BS AI tiểu đường. Tư vấn ban đầu cho bệnh nhân:\n{context}\nTrả lời ngắn gọn: 1.Kết quả 2.Rủi ro 3.Hành động 4.Ăn uống 5.Vận động 6.Khám BS. Tiếng Việt+emoji."
            use_cache = False
        else:
            # Save user message FIRST
            create_message(assessment_id, 'user', user_message)
            prompt = f"BS AI tiểu đường.\nContext:\n{context}\nCâu hỏi mới: {user_message}\nTrả lời dựa trên Hồ sơ + Lịch sử chat + Tài liệu y khoa (đã học). Ngắn gọn, VN+emoji."
            use_cache = True
        
        # Check App-level Cache
        ai_response = None
        if use_cache:
            ai_response = get_cached_response(prompt)
        
        if not ai_response:            
            # 1. Tự động lấy tên cache đang chạy
            cache_name = get_active_cache_name()
            
            if not cache_name:
                return jsonify({
                    "error": "⚠️ Hệ thống tri thức chưa được BẬT. Vui lòng chạy 'start_cache.py' trên server."
                }), 503  
            
            current_app.logger.info(f"🤖 Chat calling Gemini via Cache: {cache_name}")

            try:
                # 2. Load model TỪ CACHE (Không cần gửi file nữa)
                model = genai.GenerativeModel.from_cached_content(cached_content=cache_name)
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
                

                # 3. Chỉ gửi prompt (Tiết kiệm token & tiền)
                config = {"temperature": 0.7, "max_output_tokens": 1000}
                response = model.generate_content(prompt, generation_config=config, safety_settings=safety_settings)
                
                ai_response = response.text
                
                if use_cache:
                    cache_response(prompt, ai_response)
                    
            except Exception as e:
                current_app.logger.error(f"Gemini error: {e}")
                if "404" in str(e):
                    return jsonify({"error": "⚠️ Cache đã hết hạn. Vui lòng chạy lại 'start_cache.py'."}), 503
                if '429' in str(e):
                    return jsonify({"error": "Hệ thống bận, thử lại sau 1 phút."}), 429
                return jsonify({"error": "Lỗi AI Service"}), 500
            # ----------------------------------------------------
        
        create_message(assessment_id, 'agent', ai_response)
                
        return jsonify({
            "response": ai_response,
            "message": "Success"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/messages/assessment/<assessment_id>', methods=['GET'])
@jwt_required()
def get_messages(assessment_id):
    """Get chat history"""
    try:
        user_id = get_jwt_identity()
        assessment = get_assessment_by_id(assessment_id)
        if not assessment: return jsonify({"error": "Assessment not found"}), 404
        if str(assessment.get("user_id")) != str(user_id): return jsonify({"error": "Forbidden"}), 403
        
        messages = get_messages_by_assessment(assessment_id)
        return jsonify(messages), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/messages/assessment/<assessment_id>', methods=['DELETE'])
@jwt_required()
def delete_messages(assessment_id):
    """Delete all messages"""
    try:
        user_id = get_jwt_identity()
        assessment = get_assessment_by_id(assessment_id)
        if not assessment: return jsonify({"error": "Assessment not found"}), 404
        if str(assessment.get("user_id")) != str(user_id): return jsonify({"error": "Forbidden"}), 403
        
        count = delete_messages_by_assessment(assessment_id)
        return jsonify({"message": f"Deleted {count} messages", "deleted_count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500