import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Đã xóa SECRET_KEY, JWT_SECRET_KEY, SQLALCHEMY_DATABASE_URI
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    MOCK_MODEL_URL = os.environ.get('MOCK_MODEL_URL')