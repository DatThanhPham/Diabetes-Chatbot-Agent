from flask import Blueprint, request, jsonify
from services import UserService
from models import PyObjectId
from datasources.mongodb import get_user_collection

bp_users = Blueprint("users", __name__, url_prefix="/users")
user_service = UserService(get_user_collection())


@bp_users.post("/")
def create_user():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    existing = user_service.get_user_by_name(username)
    if existing:
        return jsonify({"error": "user already exists"}), 400

    user = user_service.create_user(username, password)
    return jsonify(
        {
            "id": str(user.id),
            "username": user.username,
            "created_at": user.created_at.isoformat(),
        }
    ), 201


@bp_users.post("/login")
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "name and password are required"}), 400

    user = user_service.authenticate(username, password)
    if not user:
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify({"user_id": str(user.id), "username": user.username})
