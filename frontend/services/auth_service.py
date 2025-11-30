"""
Authentication service
"""
from services.api_client import api_client

def register_user(username, password):
    """
    Register new user
    
    Args:
        username: Username
        password: Password
    
    Returns:
        dict: {'success': bool, 'data': {...} or 'error': str}
    """
    try:
        response = api_client.post('/users/register', json={
            'name': username,
            'password': password
        })
        
        return api_client.handle_response(response)
    except Exception as e:
        return {'success': False, 'error': str(e)}

def login_user(username, password):
    """
    Login user
    
    Args:
        username: Username
        password: Password
    
    Returns:
        dict: {'success': bool, 'data': {'user': {...}}, 'error': str}
    """
    try:
        response = api_client.post('/users/login', json={
            'name': username,
            'password': password
        })
        
        return api_client.handle_response(response)
    except Exception as e:
        return {'success': False, 'error': str(e)}