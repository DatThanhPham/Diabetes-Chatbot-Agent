from flask import Flask
from config import Config
import google.generativeai as genai
from app.predict_model import predictor

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Cấu hình Gemini API
    if not app.config['GOOGLE_API_KEY']:
        raise ValueError("GOOGLE_API_KEY không được thiết lập!")
    genai.configure(api_key=app.config['GOOGLE_API_KEY'])

    from app import routes
    app.register_blueprint(routes.bp, url_prefix='/api')

    # Khởi động model dự đoán
    with app.app_context():
        predictor.load_resources()

    return app
