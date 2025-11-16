from flask import Flask
from config import Config
import google.generativeai as genai

# Đã xóa db, migrate, jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Cấu hình Gemini API
    if not app.config['GOOGLE_API_KEY']:
        raise ValueError("GOOGLE_API_KEY không được thiết lập!")
    genai.configure(api_key=app.config['GOOGLE_API_KEY'])

    # Đăng ký các "blueprint" (API routes)
    from app import routes
    app.register_blueprint(routes.bp, url_prefix='/api')

    return app
