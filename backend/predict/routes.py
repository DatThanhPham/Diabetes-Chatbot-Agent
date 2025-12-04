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

bp = Blueprint('app_routes', __name__, url_prefix='/api')

# Cache cho RAG files
_rag_cache = {
    'files': None,
    'timestamp': None,
    'ttl': 3600  # Cache 1 hour
}

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

def get_rag_content():
    """Lấy danh sách File Reference từ ID đã cấu hình (cached with TTL)"""
    now = time.time()

    # Check if cache is valid
    if (_rag_cache['files'] is not None and 
        _rag_cache['timestamp'] is not None and 
        now - _rag_cache['timestamp'] < _rag_cache['ttl']):
        
        age = now - _rag_cache['timestamp']

        current_app.logger.info("✅ Using cached RAG files")
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
            current_app.logger.info(f"📄 Loaded RAG file: {fid}")
        except Exception as e:
            current_app.logger.error(f"Error loading file {fid}: {e}")
    
    # Update cache
    _rag_cache['files'] = tuple(rag_files)
    _rag_cache['timestamp'] = now
    
    current_app.logger.info(f"💾 Cached {len(rag_files)} RAG files")
    
    return _rag_cache['files']

def generate_response_with_files(prompt_text, user_id=None, use_cache=True):
    """Gọi Gemini với Prompt và File (có cache + rate limit)"""
    try:  
        # Rate limit
        check_rate_limit(user_id)
        
        # Check cache
        if use_cache:
            cached = get_cached_response(prompt_text)
            if cached:
                return cached
        
        rag_files = get_rag_content()
        if not rag_files:
            return "Hệ thống chưa tải tài liệu. Vui lòng kiểm tra cấu hình."

        current_app.logger.info("🤖 Calling Gemini API...")
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        content = [prompt_text] + list(rag_files)
        
        config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1500,
        }
        
        response = model.generate_content(content, generation_config=config)
        text = response.text
                
        # Cache response
        if use_cache:
            cache_response(prompt_text, text)
        
        current_app.logger.info(f"Generated {len(text)} chars")
        return text
        
    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f"Gemini error: {e}")
        
        if '429' in error_msg or 'Resource exhausted' in error_msg:
            current_app.logger.warning(f"Rate limit hit")
            return "Hệ thống bận. Vui lòng thử lại sau 2-3 phút.\n\n💡 *Các câu hỏi tương tự sẽ được cache!*"
        
        return "Xin lỗi, hệ thống đang bận. Vui lòng thử lại sau."

def build_profile_compact(record):
    """Tạo profile siêu ngắn gọn (tiết kiệm token) - khớp với DB schema"""
    if not record:
        return ""
    
    # Lấy từ metrics (theo schema DB)
    data = record.get('form_data') or record.get('metrics', {})
    pred_data = record.get('prediction', {})
    
    # Parse prediction theo schema: {prediction, risk_score, risk_level, model_version}
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
        
    # Age mapping (1-13)
    age_map = {1:"18-24",2:"25-29",3:"30-34",4:"35-39",5:"40-44",
               6:"45-49",7:"50-54",8:"55-59",9:"60-64",10:"65-69",
               11:"70-74",12:"75-79",13:"80+"}
    
    age = age_map.get(int(data.get('Age', 0)), "N/A")
    sex = "M" if data.get('Sex')==1.0 else "F"
    bmi = data.get('BMI', 0)
    
    risk_icon = "⚠️" if pred == 1 else "✅"
    factors_str = ",".join(factors) if factors else "OK"
    
    # Format: Icon|Age|Sex|BMI|RiskLevel|Factors
    profile = f"{risk_icon}{age}|{sex}|{bmi:.1f}|{risk}|{factors_str}"
    
    return profile

def build_history_compact(assessments, limit=3):
    """Tạo lịch sử 3 lần gần nhất (siêu ngắn gọn)"""
    if not assessments:
        return ""
    
    # Sort by measured_at (descending) - theo schema DB
    recent = sorted(assessments, key=lambda x: x.get('measured_at', ''), reverse=True)[:limit]
    
    print(f"Recent assessments (top {limit}):")
    for idx, a in enumerate(recent, 1):
        print(f"   {idx}. ID: {a.get('_id', 'N/A')}, Date: {str(a.get('measured_at', ''))[:19]}")
    
    lines = []
    for idx, a in enumerate(recent, 1):
        profile = build_profile_compact({
            'metrics': a.get('metrics', {}),
            'prediction': a.get('prediction', {})
        })
        # Get date from measured_at field (theo schema)
        date = str(a.get('measured_at', ''))[:10] if a.get('measured_at') else 'N/A'
        line = f"{idx}.{date}:{profile}"
        lines.append(line)
        print(f"   Line {idx}: {line}")
    
    history = "\n".join(lines)
    print(f"Generated history:\n{history}")
    print(f"{'='*70}\n")
    
    return history

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
            
            print(f"Prediction: {prediction}, Risk score: {risk_score:.2%}")
            current_app.logger.info(f"Prediction: {prediction}, Risk: {risk_score:.2%}")
            
        except Exception as e:
            current_app.logger.error(f"Model error: {e}")
            return jsonify({"error": f"Lỗi mô hình: {str(e)}"}), 500

        return jsonify({
            "prediction": int(prediction),
            "risk_level": "high" if prediction == 1 else "low",
            "risk_score": risk_score,
            "validated_data": validated_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Analyze error: {e}")
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
        
        # Prompt siêu ngắn (tiết kiệm token)
        prompt = f"""BS AI tiểu đường. Tư vấn cho:
{profile}

Trả lời ngắn:
1.Kết quả
2.Rủi ro chính
3.3-5 hành động
4.Ăn uống
5.Vận động
6.Khám BS

Tiếng Việt+emoji, ngắn gọn."""
        
        current_app.logger.info("🤖 Generating advice...")
        advice = generate_response_with_files(prompt, user_id, use_cache=False)
        current_app.logger.info(f"{len(advice)} chars")

        assessment_id = None
        if user_id:
            try:
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
                    current_app.logger.info(f"Assessment: {assessment_id}")
                    
                    msg_result = create_message(
                        assessment_id=assessment_id,
                        sender_type='agent',
                        content=advice,
                        metadata={'type': 'initial_advice'}
                    )
                    
                    if msg_result.get('success'):
                        current_app.logger.info("Message saved")
                
            except Exception as e:
                current_app.logger.error(f"DB error: {e}")
                current_app.logger.error(traceback.format_exc())

        return jsonify({
            "advice": advice,
            "assessment_id": assessment_id,
            "prediction": int(prediction),
            "risk_score": float(risk_score),
            "risk_level": "high" if prediction == 1 else "low"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500