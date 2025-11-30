from flask import Blueprint, request, jsonify, current_app
from services.assessment_service import (
    create_assessment, 
    get_assessments_by_user, 
    get_assessment_by_id,
    get_latest_valid_assessment,
    get_latest_assessment
)
from predict import predictor, validate_form_data, sanitize_form_data

bp = Blueprint('assessments', __name__, url_prefix='/api/assessments')

@bp.route('', methods=['POST'])
def create_new_assessment():
    """Create new assessment with prediction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        form_data = data.get('form_data')
        
        if not user_id or not form_data:
            return jsonify({"error": "user_id and form_data are required"}), 400
        
        # Sanitize form data
        form_data = sanitize_form_data(form_data)
        
        # Validate form data
        is_valid, error_msg = validate_form_data(form_data)
        if not is_valid:
            return jsonify({"error": f"Validation error: {error_msg}"}), 400
        
        # Make prediction using the model
        prediction = predictor.predict(form_data)
        current_app.logger.info(f"Prediction for user {user_id}: {prediction}")
        
        # Get probability if available
        try:
            proba = predictor.predict_proba(form_data)
            risk_score = proba.get('high_risk', float(prediction))
            current_app.logger.info(f"Risk probabilities: {proba}")
        except Exception as e:
            current_app.logger.warning(f"Could not get probabilities: {e}")
            risk_score = float(prediction)
        
        # Save to DB (will invalidate previous assessments)
        assessment_id = create_assessment(user_id, form_data, int(prediction), risk_score)
        assessment = get_assessment_by_id(assessment_id)
        
        return jsonify({
            "assessment": assessment,
            "message": "Assessment created successfully"
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Assessment creation error: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/user/<user_id>', methods=['GET'])
def get_user_assessments(user_id):
    """Get all assessments of a user"""
    try:
        valid_only = request.args.get('valid_only', 'false').lower() == 'true'
        assessments = get_assessments_by_user(user_id, valid_only=valid_only)
        return jsonify(assessments), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/user/<user_id>/latest', methods=['GET'])
def get_user_latest_assessment(user_id):
    """Get latest assessment of user"""
    try:
        # Check if we want valid only
        valid_only = request.args.get('valid_only', 'true').lower() == 'true'
        
        if valid_only:
            assessment = get_latest_valid_assessment(user_id)
        else:
            assessment = get_latest_assessment(user_id)
        
        if not assessment:
            return jsonify({"error": "No assessment found"}), 404
        return jsonify(assessment), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<assessment_id>', methods=['GET'])
def get_assessment(assessment_id):
    """Get assessment by ID"""
    try:
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({"error": "Assessment not found"}), 404
        return jsonify(assessment), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/predict', methods=['POST'])
def predict_only():
    """Predict without saving to database (for testing)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        form_data = data.get('form_data')
        if not form_data:
            return jsonify({"error": "form_data is required"}), 400
        
        # Sanitize form data
        form_data = sanitize_form_data(form_data)
        
        # Validate form data
        is_valid, error_msg = validate_form_data(form_data)
        if not is_valid:
            return jsonify({"error": f"Validation error: {error_msg}"}), 400
        
        # Make prediction
        prediction = predictor.predict(form_data)
        
        # Get probabilities
        try:
            proba = predictor.predict_proba(form_data)
        except:
            proba = {
                "low_risk": 0.0 if prediction == 1 else 1.0,
                "high_risk": 1.0 if prediction == 1 else 0.0
            }
        
        return jsonify({
            "prediction": int(prediction),
            "risk_level": "high" if prediction == 1 else "low",
            "probabilities": proba,
            "form_data": form_data  # Return sanitized data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/validate', methods=['POST'])
def validate_data():
    """Validate form data without prediction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        form_data = data.get('form_data')
        if not form_data:
            return jsonify({"error": "form_data is required"}), 400
        
        # Sanitize
        sanitized_data = sanitize_form_data(form_data)
        
        # Validate
        is_valid, error_msg = validate_form_data(sanitized_data)
        
        if is_valid:
            return jsonify({
                "valid": True,
                "message": "Form data is valid",
                "sanitized_data": sanitized_data
            }), 200
        else:
            return jsonify({
                "valid": False,
                "error": error_msg,
                "sanitized_data": sanitized_data
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 500