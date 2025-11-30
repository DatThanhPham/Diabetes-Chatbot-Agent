"""
API Client for backend communication
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')

class APIClient:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def post(self, endpoint, data=None, json=None):
        """POST request"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, data=data, json=json, timeout=30)
            return response
        except requests.exceptions.Timeout:
            raise Exception("Request timeout - Server không phản hồi")
        except requests.exceptions.ConnectionError:
            raise Exception("Không thể kết nối đến server")
    
    def get(self, endpoint, params=None):
        """GET request"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            return response
        except requests.exceptions.Timeout:
            raise Exception("Request timeout - Server không phản hồi")
        except requests.exceptions.ConnectionError:
            raise Exception("Không thể kết nối đến server")
    
    def handle_response(self, response):
        """Handle API response"""
        try:
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except requests.exceptions.HTTPError as e:
            error_msg = 'Unknown error'
            try:
                error_data = response.json()
                error_msg = error_data.get('error', str(e))
            except:
                error_msg = str(e)
            
            return {'success': False, 'error': error_msg}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global API client instance
api_client = APIClient()