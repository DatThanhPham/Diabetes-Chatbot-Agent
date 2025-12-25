"""
Assessment service
"""
from services.api_client import api_client

def analyze_risk(form_data):
    """
    Analyze health risk
    
    Args:
        form_data: dict with 19 health metrics
    
    Returns:
        dict: {'success': bool, 'data': {'prediction', 'risk_score', ...}, 'error': str}
    """
    try:
        response = api_client.post('/analyze_risk', json=form_data)
        return api_client.handle_response(response)
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_advice(validated_data, prediction, risk_score, user_id=None):
    """
    Get AI advice
    
    Args:
        validated_data: Validated health data
        prediction: 0 or 1
        risk_score: 0.0 - 1.0
        user_id: User ID (optional)
    
    Returns:
        dict: {'success': bool, 'data': {'advice', 'assessment_id'}, 'error': str}
    """
    try:
        response = api_client.post('/get_advice', json={
            'validated_data': validated_data,
            'prediction': prediction,
            'risk_score': risk_score,
            'user_id': user_id
        })
        
        return api_client.handle_response(response)
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user_assessments(user_id, valid_only=False):
    """
    Get all assessments of user
    
    Args:
        user_id: User ID
        valid_only: Only get valid assessments
    
    Returns:
        dict: {'success': bool, 'data': [...], 'error': str}
    """
    try:
        params = {'valid_only': 'true'} if valid_only else {}
        response = api_client.get(f'/assessments/user/{user_id}', params=params)
        
        return api_client.handle_response(response)
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_assessment_by_id(assessment_id):
    """
    Get assessment by ID
    
    Args:
        assessment_id: Assessment ID
    
    Returns:
        dict: {'success': bool, 'data': {...}, 'error': str}
    """
    try:
        response = api_client.get(f'/assessments/{assessment_id}')
        return api_client.handle_response(response)
    except Exception as e:
        return {'success': False, 'error': str(e)}