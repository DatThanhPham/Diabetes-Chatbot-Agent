import time
import hashlib
from flask import Blueprint, request, jsonify, current_app
from predict.validation import validate_health_form
from predict.predict_model import predictor
from services.assessment_service import create_assessment, get_assessment_by_id, get_assessments_by_user
from services.message_service import create_message
import google.generativeai as genai
import traceback 
import json
import os
from google.generativeai.types import HarmCategory, HarmBlockThreshold


bp = Blueprint('app_routes', __name__, url_prefix='/api')

# Cache cho responses
_response_cache = {}
_response_cache_ttl = 300  # 5 minutes
_response_cache_max_size = 100

# Cache statistics
_cache_stats = {
    'hits': 0,
    'misses': 0,
    'total_calls': 0
}

# Rate limiting
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
            current_app.logger.info(f"Cache hit: {cache_key[:8]}, hit rate: {hit_rate:.1f}%")
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
            current_app.logger.warning(f"⏳ Rate limit: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
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

def generate_response_with_files(prompt_text, user_id=None, use_cache=True):
    try:
        check_rate_limit(user_id)
        
        if use_cache:
            cached = get_cached_response(prompt_text)
            if cached: 
                current_app.logger.info(f"⚡ Cache hit")
                return cached

        cache_name = get_active_cache_name()
        
        if not cache_name:
            return "⚠️ Hệ thống tri thức chưa được BẬT."

        current_app.logger.info(f"🤖 Calling Gemini via Cache: {cache_name}")

        try:
            model = genai.GenerativeModel.from_cached_content(cached_content=cache_name)
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            # ✅ FIX: Dùng candidate_count=1 và KHÔNG SET max_output_tokens
            # Để Gemini tự quyết định độ dài output dựa trên prompt
            generate_config = genai.types.GenerationConfig(
                # ❌ KHÔNG SET: max_output_tokens=500,  
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                candidate_count=1,  # ✅ Chỉ sinh 1 candidate
            )

            current_app.logger.info(f"📝 Prompt length: {len(prompt_text)} chars")

            response = model.generate_content(
                prompt_text, 
                safety_settings=safety_settings, 
                generation_config=generate_config
            )

            if not response.candidates:
                current_app.logger.error(f"❌ Blocked: {response.prompt_feedback}")
                return "Xin lỗi, hệ thống không thể tạo lời khuyên."
            
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason
            
            # Mapping finish_reason
            finish_map = {
                0: "UNSPECIFIED",
                1: "STOP",
                2: "MAX_TOKENS",
                3: "SAFETY",
                4: "RECITATION",
                5: "OTHER"
            }
            
            finish_str = finish_map.get(finish_reason, str(finish_reason))
            current_app.logger.info(f"🏁 Finish: {finish_str}")
            
            if finish_reason == 2:
                current_app.logger.error(f"❌ MAX_TOKENS! Response may be truncated.")
            elif finish_reason not in [1, 'STOP']:
                current_app.logger.warning(f"⚠️ Early finish: {finish_str}")

            try:
                text = response.text
            except Exception as e:
                current_app.logger.error(f"Error .text: {e}")
                try:
                    text = candidate.content.parts[0].text
                except:
                    return "Xin lỗi, không thể tạo lời khuyên."

            if response.usage_metadata:
                total = response.usage_metadata.prompt_token_count
                cached_cnt = response.usage_metadata.cached_content_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                
                current_app.logger.info(
                    f"📊 Tokens: prompt={total} (cache={cached_cnt}, new={total-cached_cnt}), "
                    f"OUTPUT={output_tokens}"
                )
            
            current_app.logger.info(f"✅ Response: {len(text)} chars, {len(text.split())} words")
            
            if use_cache:
                cache_response(prompt_text, text)
                
            return text

        except Exception as e:
            error_msg = str(e)
            current_app.logger.error(f"Gemini error: {error_msg}\n{traceback.format_exc()}")
            
            if "404" in error_msg or "not found" in error_msg.lower():
                return "⚠️ Cache hết hạn. Chạy lại 'start_cache.py'."
            if '429' in error_msg or 'Resource exhausted' in error_msg:
                return "Hệ thống bận. Thử lại sau 1 phút."
            raise e
        
    except Exception as e:
        current_app.logger.error(f"Gemini error: {e}")
        return "Xin lỗi, hệ thống đang bận."    

def build_profile_compact(record):
    """
    Output:
    - Giới tính: Nam (50-54 tuổi)
    - BMI: 28.5 (Thừa cân)
    - Tình trạng: Cao huyết áp, Cholesterol cao, Ít vận động
    - Dự đoán: Nguy cơ CAO
    """
    if not record:
        return ""
    
    # 1. Lấy dữ liệu
    data = record.get('form_data') or record.get('metrics', {})
    pred_data = record.get('prediction', {})
    
    # 2. Xử lý Prediction
    if isinstance(pred_data, dict):
        pred = pred_data.get('prediction', 0)
        risk_level = "CAO ⚠️" if pred == 1 else "THẤP ✅"

    else:
        pred = pred_data
        risk_level = "CAO ⚠️" if pred == 1 else "THẤP ✅"

    # 3. Mapping thông tin cơ bản
    # Age mapping
    age_map = {1:"18-24",2:"25-29",3:"30-34",4:"35-39",5:"40-44",
               6:"45-49",7:"50-54",8:"55-59",9:"60-64",10:"65-69",
               11:"70-74",12:"75-79",13:"80+"}
    age_str = age_map.get(int(data.get('Age', 0)), "N/A")
    
    sex_str = "Nam" if data.get('Sex') == 1.0 else "Nữ"
    
    # 4. Xử lý BMI chi tiết hơn
    bmi = data.get('BMI', 0)
    bmi_status = ""
    if bmi < 18.5: bmi_status = "(Thiếu cân)"
    elif 18.5 <= bmi < 25: bmi_status = "(Bình thường)"
    elif 25 <= bmi < 30: bmi_status = "(Thừa cân)"
    else: bmi_status = "(Béo phì)"
    
    # 5. Xử lý các yếu tố nguy cơ (Risk Factors) sang Tiếng Việt
    factors = []
    
    # Mapping dictionary cho gọn code
    risk_map = {
        'HighBP': "Cao huyết áp",
        'HighChol': "Cholesterol cao (Mỡ máu)",
        'Smoker': "Hút thuốc lá",
        'HeartDiseaseorAttack': "Tiền sử bệnh tim/nhồi máu",
        'Stroke': "Tiền sử đột quỵ"
    }
    
    for key, label in risk_map.items():
        if data.get(key) == 1.0:
            factors.append(label)
            
    # Xử lý riêng PhysActivity (0 là xấu)
    if data.get('PhysActivity') == 0.0:
        factors.append("Lười vận động/Ít thể dục")

    factors_str = ", ".join(factors) if factors else "Không có ghi nhận đặc biệt"

    # 6. TẠO STRING FINAL (Format dạng YAML/List để AI dễ đọc nhất)
    profile = (
        f"- Bệnh nhân: {sex_str}, {age_str} tuổi\n"
        f"- Chỉ số BMI: {bmi:.1f} {bmi_status}\n"
        f"- Yếu tố nguy cơ ghi nhận: {factors_str}\n"
        f"- Kết quả mô hình dự đoán: Nguy cơ {risk_level}"
    )
    
    return profile

def build_history_compact(assessments, limit=3):
    if not assessments: return ""
    recent = sorted(assessments, key=lambda x: x.get('measured_at', ''), reverse=True)[:limit]
    lines = []
    for idx, a in enumerate(recent, 1):
        profile = build_profile_compact({
            'metrics': a.get('metrics', {}),
            'prediction': a.get('prediction', {})
        })
        date = str(a.get('measured_at', ''))[:10] if a.get('measured_at') else 'N/A'
        lines.append(f"{idx}.{date}:{profile}")
    return "\n".join(lines)

@bp.route('/analyze_risk', methods=['POST'])
def analyze_risk():
    """Bước 1: Validate + Predict (không lưu DB)"""
    try:
        form_data = request.get_json()
        is_valid, result = validate_health_form(form_data)
        if not is_valid: return jsonify({"error": result}), 400
        
        validated_data = result
        try:
            if predictor is None: raise RuntimeError("Predictor not initialized")
            prediction = predictor.predict(validated_data)
            try:
                proba = predictor.predict_proba(validated_data)
                risk_score = proba.get('high_risk', float(prediction))
            except: risk_score = float(prediction)
        except Exception as e:
            return jsonify({"error": f"Lỗi mô hình: {str(e)}"}), 500

        return jsonify({
            "prediction": int(prediction),
            "risk_level": "high" if prediction == 1 else "low",
            "risk_score": risk_score,
            "validated_data": validated_data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/get_advice', methods=['POST'])
def get_advice():
    """Bước 2: Generate advice (lưu DB theo schema)"""
    try:
        data = request.get_json()
        validated_data = data.get('validated_data')
        prediction = data.get('prediction')
        user_id = data.get('user_id')
        risk_score = data.get('risk_score', float(prediction))

        current_app.logger.info(f"📥 Advice: user={user_id}, pred={prediction}")

        if validated_data is None or prediction is None:
            return jsonify({"error": "Thiếu dữ liệu"}), 400

        # Build compact profile
        profile = build_profile_compact({
            'form_data': validated_data,
            'prediction': prediction
        })
        
        # Prompt
        prompt = f"""Bạn là trợ lý chăm sóc sức khỏe AI. Dựa vào hồ sơ bệnh nhân sau:

{profile}

YÊU CẦU: Hãy viết một bản tư vấn CHI TIẾT (ít nhất 300 từ), bao gồm:

1. 📋 Đánh giá tổng quan tình trạng sức khỏe (2-3 câu)
2. ⚠️ Các yếu tố nguy cơ cần lưu ý (3-4 điểm)
3. 🥗 Gợi ý dinh dưỡng cụ thể (4-5 điểm với ví dụ thực phẩm)
4. 🏃 Gợi ý vận động phù hợp (3-4 điểm với cường độ, thời lượng)
5. 🩺 Khi nào cần gặp bác sĩ (2-3 dấu hiệu)
6. 💡 Lời khuyên thêm (1-2 điểm)

Format: Dùng bullet points, emoji, VIẾT ĐẦY ĐỦ các mục trên.

BẮT ĐẦU TƯ VẤN:"""
        
        current_app.logger.info("🤖 Generating advice...")
        
        # Gọi hàm đã được tối ưu cache
        advice = generate_response_with_files(prompt, user_id, use_cache=False)
        
        current_app.logger.info(f"{len(advice)} chars")

        assessment_id = None
        if user_id:
            try:
                # ... (Giữ nguyên logic lưu DB) ...
                risk_level = 'high' if prediction == 1 else 'low'
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
                if result.get('success'):
                    assessment_id = result['data']['id']
                    create_message(
                        assessment_id=assessment_id,
                        sender_type='agent',
                        content=advice,
                        metadata={'type': 'initial_advice'}
                    )
            except Exception as e:
                current_app.logger.error(f"DB error: {e}")

        return jsonify({
            "advice": advice,
            "assessment_id": assessment_id,
            "prediction": int(prediction),
            "risk_score": float(risk_score),
            "risk_level": "high" if prediction == 1 else "low"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500