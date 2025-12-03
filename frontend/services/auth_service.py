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
        
        result = api_client.handle_response(response)
        if result.get('success'):
            data = result['data']
            access_token = data.get('access_token')
            if access_token:
                api_client.set_auth_token(access_token)
        
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
def logout_user():
    api_client.set_auth_token(None)
    return {'success': True}