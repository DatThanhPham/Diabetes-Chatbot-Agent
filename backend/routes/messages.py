from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.message_service import create_message, get_messages_by_assessment
from services.assessment_service import get_assessment_by_id, get_assessments_by_user
import google.generativeai as genai
import time
import hashlib

bp = Blueprint('messages', __name__, url_prefix='/api')

# Cache settings
_rag_cache = {
    'files': None,
    'timestamp': None,
    'ttl': 3600  # 1 hour
}

_response_cache = {}
_response_cache_ttl = 300  # 5 minutes
_response_cache_max_size = 100

_cache_stats = {
    'hits': 0,
    'misses': 0,
    'total_calls': 0
}

_rate_limiter = {}
MIN_REQUEST_INTERVAL = 2  # seconds

def get_cache_key(prompt_text):
    """Generate cache key from prompt"""
    return hashlib.md5(prompt_text.encode('utf-8')).hexdigest()

def get_cached_response(prompt_text):
    """Get cached response if exists and valid"""
    _cache_stats['total_calls'] += 1
    cache_key = get_cache_key(prompt_text)
    
    if cache_key in _response_cache:
        cached = _response_cache[cache_key]
        age = time.time() - cached['timestamp']
        
        if age < _response_cache_ttl:
            _cache_stats['hits'] += 1
            hit_rate = (_cache_stats['hits'] / _cache_stats['total_calls']) * 100
            
            return cached['response']
        else:
            del _response_cache[cache_key]
    
    _cache_stats['misses'] += 1
    return None

def cache_response(prompt_text, response_text):
    """Cache a response"""
    if len(_response_cache) >= _response_cache_max_size:
        oldest_key = min(_response_cache.keys(), key=lambda k: _response_cache[k]['timestamp'])
        del _response_cache[oldest_key]
    
    cache_key = get_cache_key(prompt_text)
    _response_cache[cache_key] = {
        'response': response_text,
        'timestamp': time.time()
    }
    
def check_rate_limit(user_id):
    """Check and enforce rate limiting"""
    if not user_id:
        return
    
    now = time.time()
    if user_id in _rate_limiter:
        time_diff = now - _rate_limiter[user_id]
        
        if time_diff < MIN_REQUEST_INTERVAL:
            wait_time = MIN_REQUEST_INTERVAL - time_diff
            time.sleep(wait_time)
    
    _rate_limiter[user_id] = time.time()

def get_rag_content():
    """Get RAG files (cached)"""
    now = time.time()
    
    if (_rag_cache['files'] is not None and 
        _rag_cache['timestamp'] is not None and 
        now - _rag_cache['timestamp'] < _rag_cache['ttl']):
        
        age = now - _rag_cache['timestamp']
        return _rag_cache['files']
    
    file_ids_str = current_app.config.get('KNOWLEDGE_FILE_IDS', '')
    if not file_ids_str:
        return tuple()
    
    file_id_list = [fid.strip() for fid in file_ids_str.split(',') if fid.strip()]
    rag_files = []
    
    for file_id in file_id_list:
        try:
            file_obj = genai.get_file(file_id)
            rag_files.append(file_obj)
        except Exception as e:
            current_app.logger.warning(f"Error fetching RAG file {file_id}: {e}")
    
    _rag_cache['files'] = tuple(rag_files)
    _rag_cache['timestamp'] = now

    return _rag_cache['files']

def build_profile_compact(record):
    """Build compact profile string"""
    if not record:
        return ""
    
    data = record.get('metrics', {})
    pred_data = record.get('prediction', {})
    
    if isinstance(pred_data, dict):
        pred = pred_data.get('prediction', 0)
        risk = pred_data.get('risk_level', 'low')
    else:
        pred = pred_data
        risk = 'high' if pred == 1 else 'low'
    
    # Extract risk factors
    factors = []
    if data.get('HighBP') == 1.0: factors.append("HA")
    if data.get('HighChol') == 1.0: factors.append("Chol")
    if data.get('BMI', 0) >= 25: factors.append(f"BMI{data.get('BMI'):.0f}")
    if data.get('Smoker') == 1.0: factors.append("Smoke")
    if data.get('PhysActivity') == 0.0: factors.append("NoEx")
    if data.get('HeartDiseaseorAttack') == 1.0: factors.append("Heart")
    if data.get('Stroke') == 1.0: factors.append("Stroke")
    
    # Age mapping
    age_map = {1:"18-24",2:"25-29",3:"30-34",4:"35-39",5:"40-44",
               6:"45-49",7:"50-54",8:"55-59",9:"60-64",10:"65-69",
               11:"70-74",12:"75-79",13:"80+"}
    
    age = age_map.get(int(data.get('Age', 0)), "N/A")
    sex = "M" if data.get('Sex')==1.0 else "F"
    bmi = data.get('BMI', 0)
    
    risk_icon = "⚠️" if pred == 1 else "✅"
    factors_str = ",".join(factors) if factors else "OK"
    
    return f"{risk_icon}{age}|{sex}|{bmi:.1f}|{risk}|{factors_str}"

def build_history_compact(assessments, limit=3):
    """Build compact history of recent assessments"""
    if not assessments:
        return ""
    
    # Sort by measured_at (descending)
    recent = sorted(assessments, key=lambda x: x.get('measured_at', ''), reverse=True)[:limit]
    
    lines = []
    for idx, a in enumerate(recent, 1):
        profile = build_profile_compact(a)
        date = str(a.get('measured_at', ''))[:10]
        lines.append(f"{idx}.{date}:{profile}")
    
    return "\n".join(lines)

def build_chat_history_context(messages, limit=3):
    """Build chat history context from messages"""
    if not messages:
        return ""
    
    # Get recent messages (last N messages)
    recent_messages = messages[-limit:] if len(messages) > limit else messages
        
    lines = []
    for msg in recent_messages:
        sender = msg.get('sender_type', 'unknown')
        content = msg.get('content', '')
        
        if sender == 'user':
            lines.append(f"Bệnh nhân: {content}")
        else:
            lines.append(f"Bác sĩ: {content}")
    
    history = "\n".join(lines)
    
    return history

@bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """Chat with AI - with full context: assessment + 3 recent assessments + current chat history"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        assessment_id = data.get('assessment_id')
        user_message = data.get('user_message')
        
        if not assessment_id:
            return jsonify({"error": "assessment_id is required"}), 400
        
        # Get assessment
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({"error": "Assessment not found"}), 404
        
        user_id = get_jwt_identity()
        
        # Check ownership
        if str(assessment.get("user_id")) != str(user_id):
            return jsonify({"error": "Forbidden"}), 403
        
        # Apply rate limiting
        check_rate_limit(user_id)
        
        # Build context
        context_lines = []
        
        # 1. Current assessment
        profile = build_profile_compact(assessment)
        context_lines.append(f"Đánh giá hiện tại:{profile}")
        
        # 2. Get 3 recent assessments for history
        try:
            result = get_assessments_by_user(user_id, valid_only=False)
            if result.get('success'):
                assessments = result.get('data', [])

                if len(assessments) > 1:
                    history = build_history_compact(assessments, limit=3)
                    if history:
                        context_lines.append(f"Lịch sử 3 lần đánh giá:\n{history}")
        except Exception as e:
            print(f"Assessment history error: {e}")
        
        # 3. Get current chat history (messages in this assessment)
        try:
            chat_messages = get_messages_by_assessment(assessment_id)
            
            if chat_messages:
                chat_history = build_chat_history_context(chat_messages, limit=10)
                if chat_history:
                    context_lines.append(f"Lịch sử chat hiện tại (10 tin gần nhất):\n{chat_history}")
        except Exception as e:
            print(f"Chat history error: {e}")
        
        context = "\n\n".join(context_lines)
        
        # Generate prompt
        if user_message is None:
            # Initial advice
            prompt = f"""BS AI tiểu đường. Tư vấn ban đầu cho bệnh nhân:

{context}

Trả lời ngắn gọn:
1.Kết quả đánh giá
2.Rủi ro chính
3.3-5 hành động cần làm
4.Chế độ ăn uống
5.Vận động
6.Khám bác sĩ

Tiếng Việt+emoji, thân thiện."""
            use_cache = False  # Don't cache personalized advice
        else:
            # Save user message first
            user_msg_result = create_message(assessment_id, 'user', user_message)
            if not user_msg_result.get('success'):
                current_app.logger.error(f"Failed to save user message")
            
            prompt = f"""BS AI tiểu đường.

Context bệnh nhân:
{context}

Câu hỏi mới: {user_message}

Trả lời dựa trên:
- Thông tin đánh giá hiện tại
- Lịch sử 3 lần đánh giá gần nhất
- Lịch sử chat trong assessment này
- Kiến thức y khoa

Ngắn gọn, thực tế, VN+emoji."""
            use_cache = True  # Cache common questions (but with different context = different cache key)
        
        # Check cache first (note: cache key includes full context, so different chats won't collide)
        ai_response = None
        if use_cache:
            ai_response = get_cached_response(prompt)
        
        if not ai_response:
            # Call Gemini
            rag_files = get_rag_content()
            
            if not rag_files:
                return jsonify({"error": "RAG files not available"}), 500
                        
            model = genai.GenerativeModel('gemini-2.0-flash')
            content = [prompt] + list(rag_files)
            
            config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1500,
            }
            
            try:
                response = model.generate_content(content, generation_config=config)
                ai_response = response.text
                                
                # Cache response
                if use_cache:
                    cache_response(prompt, ai_response)
                    
            except Exception as e:
                error_msg = str(e)
                print(f"Gemini error: {e}")
                
                if '429' in error_msg or 'Resource exhausted' in error_msg:
                    return jsonify({
                        "error": "Hệ thống bận. Vui lòng thử lại sau 2-3 phút.\n\n💡 *Các câu hỏi tương tự sẽ được cache!*"
                    }), 429
                
                return jsonify({"error": f"Lỗi AI: {str(e)}"}), 500
        
        # Save AI message
        create_message(assessment_id, 'agent', ai_response)
                
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
    """Get chat history"""
    try:
        user_id = get_jwt_identity()
        assessment = get_assessment_by_id(assessment_id)
        
        if not assessment:
            return jsonify({"error": "Assessment not found"}), 404

        if str(assessment.get("user_id")) != str(user_id):
            return jsonify({"error": "Forbidden"}), 403
        
        messages = get_messages_by_assessment(assessment_id)
        return jsonify(messages), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/messages/assessment/<assessment_id>', methods=['DELETE'])
@jwt_required()
def delete_messages(assessment_id):
    """Delete all messages"""
    try:
        from services.message_service import delete_messages_by_assessment
        user_id = get_jwt_identity()
        assessment = get_assessment_by_id(assessment_id)
        
        if not assessment:
            return jsonify({"error": "Assessment not found"}), 404

        if str(assessment.get("user_id")) != str(user_id):
            return jsonify({"error": "Forbidden"}), 403
        
        count = delete_messages_by_assessment(assessment_id)
        return jsonify({
            "message": f"Deleted {count} messages",
            "deleted_count": count
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500