import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_CLUSTER = os.getenv("DB_CLUSTER")
    DB_NAME = os.getenv("DB_NAME", "DCA_DB")
    
    #JWT_SECRET_KEY
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")  
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Đã xóa SECRET_KEY, JWT_SECRET_KEY, SQLALCHEMY_DATABASE_URI
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    KNOWLEDGE_FILE_IDS = os.environ.get('KNOWLEDGE_FILE_IDS')
    MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', '../models')
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'stacking_ensemble_model.bin')
