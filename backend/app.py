from flask import Flask
from flask_cors import CORS
from config import Config
import google.generativeai as genai
import os
import logging
from flask_jwt_extended import JWTManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    jwt = JWTManager(app)
    
    # Enable CORS for Streamlit
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configure Gemini AI
    if app.config['GEMINI_API_KEY']:
        genai.configure(api_key=app.config['GEMINI_API_KEY'])
        app.logger.info("✓ Gemini API configured")
    else:
        app.logger.warning("⚠ GEMINI_API_KEY not set!")
    
    # Register blueprints
    from routes.users import bp as users_bp
    from routes.assessments import bp as assessments_bp
    from routes.messages import bp as messages_bp
    from predict.routes import bp as app_routes_bp
    
    app.register_blueprint(users_bp)
    app.register_blueprint(assessments_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(app_routes_bp)
    
    app.logger.info("✓ All blueprints registered")
    
    @app.route('/')
    def health_check():
        return {
            "status": "ok", 
            "message": "Diabetes Chatbot API is running",
            "version": "2.0",
            "endpoints": {
                "users": {
                    "register": "POST /api/users/register",
                    "login": "POST /api/users/login",
                    "get": "GET /api/users/{user_id}"
                },
                "assessments": {
                    "create": "POST /api/assessments",
                    "get_user_assessments": "GET /api/assessments/user/{user_id}",
                    "get_latest": "GET /api/assessments/user/{user_id}/latest",
                    "get_by_id": "GET /api/assessments/{assessment_id}",
                    "predict_only": "POST /api/assessments/predict",
                    "validate": "POST /api/assessments/validate"
                },
                "chat": {
                    "chat": "POST /api/chat",
                    "get_messages": "GET /api/messages/assessment/{assessment_id}",
                    "delete_messages": "DELETE /api/messages/assessment/{assessment_id}"
                },
                "rag_flow": {
                    "analyze_risk": "POST /api/analyze_risk",
                    "get_advice": "POST /api/get_advice",
                }
            }
        }, 200
    
    @app.route('/api/health')
    def api_health():
        """Check API health and dependencies"""
        from datasources.mongodb import test_connection
        
        mongo_status = test_connection()
        gemini_status = bool(app.config.get('GEMINI_API_KEY'))
        model_exists = os.path.exists(app.config['MODEL_PATH'])
        
        rag_files = []
        if app.config.get('KNOWLEDGE_FILE_IDS'):
            rag_files = [fid.strip() for fid in app.config['KNOWLEDGE_FILE_IDS'].split(',') if fid.strip()]
        
        return {
            "mongodb": "connected" if mongo_status else "disconnected",
            "gemini": "configured" if gemini_status else "not configured",
            "model": {
                "exists": model_exists,
                "path": app.config['MODEL_PATH']
            },
            "rag": {
                "configured": len(rag_files) > 0,
                "file_count": len(rag_files)
            }
        }, 200
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.logger.info("=" * 60)
    app.logger.info("🚀 Starting Diabetes Chatbot Backend")
    app.logger.info("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)