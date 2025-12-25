"""
Chat Service - API calls for chat functionality
"""
from services.api_client import api_client

def send_message(assessment_id, message):
    """
    Send chat message and get AI response
    
    Args:
        assessment_id: Assessment ID
        message: User message
    
    Returns:
        dict: {'success': bool, 'data': {'response': str}, 'error': str}
    """
    try:
        payload = {
            'assessment_id': assessment_id,
            'user_message': message
        }
        
        response = api_client.post('/chat', json=payload)
        return api_client.handle_response(response)
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_messages_by_assessment(assessment_id):
    """
    Get chat history for an assessment
    
    Returns:
        dict: {'success': bool, 'data': [...], 'error': str}
    """
    try:
        response = api_client.get(f'/messages/assessment/{assessment_id}')
        return api_client.handle_response(response)
    except Exception as e:
        return {'success': False, 'error': str(e)}