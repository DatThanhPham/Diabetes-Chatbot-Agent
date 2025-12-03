from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from services.user_service import create_user, validate_user, get_user_by_id

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name') or data.get('username')  # Support both
        password = data.get('password')
        
        if not name or not password:
            return jsonify({"error": "Name and password are required"}), 400
        
        user_id = create_user(name, password)
        return jsonify({
            "user_id": user_id, 
            "message": "User created successfully"
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name') or data.get('username')  # Support both
        password = data.get('password')
        
        if not name or not password:
            return jsonify({"error": "Name and password are required"}), 400
        
        user = validate_user(name, password)
        access_token = create_access_token(identity=user["id"])
        refresh_token = create_refresh_token(identity=user["id"])
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user, 
            "message": "Login successful"
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"user": user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
   
@bp.post("/refresh")    
@jwt_required(refresh=True)
def refresh_access_token():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": new_access_token}), 200    