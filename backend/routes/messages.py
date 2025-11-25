from flask import Blueprint, request, jsonify
from services import MessageService
from models import PyObjectId
from datasources.mongodb import get_message_collection

bp_chat = Blueprint("chat", __name__, url_prefix="/chat")
chat_service = MessageService(get_message_collection())


@bp_chat.post("/messages")
def add_message_route():
    data = request.json or {}
    user_id = data.get("user_id")
    content = data.get("content")
    sender_type = data.get("sender_type", "user")
    assessment_id = data.get("assessment_id")
    metadata = data.get("metadata")

    if not user_id or not content:
        return jsonify({"error": "user_id and content are required"}), 400

    msg = chat_service.add_message(
        user_id=PyObjectId(user_id),
        content=content,
        sender_type=sender_type,
        assessment_id=PyObjectId(assessment_id) if assessment_id else None,
        metadata=metadata,
    )
    return jsonify(msg.dict(by_alias=True)), 201


@bp_chat.get("/messages")
def list_messages_route():
    user_id = request.args.get("user_id")
    limit = int(request.args.get("limit", 50))

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    messages = chat_service.list_messages_by_user(
        user_id=PyObjectId(user_id),
        limit=limit,
    )
    return jsonify([m.dict(by_alias=True) for m in messages])
