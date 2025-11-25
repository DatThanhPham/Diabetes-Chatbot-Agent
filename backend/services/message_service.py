from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from models import Message, PyObjectId


class MessageService:
    def __init__(self, chat_col):
        self.col = chat_col

    def _doc_to_message(self, doc) -> Message:
        return Message(**doc)

    def add_message(
        self,
        user_id: PyObjectId,
        content: str,
        sender_type: str = "user",
        assessment_id: Optional[PyObjectId] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        now = datetime.utcnow()
        doc = {
            "user_id": ObjectId(user_id),
            "assessment_id": ObjectId(assessment_id) if assessment_id else None,
            "sender_type": sender_type,
            "content": content,
            "created_at": now,
            "metadata": metadata or {},
        }
        result = self.col.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._doc_to_message(doc)

    def list_messages_by_user(self, user_id: PyObjectId, limit: int = 50) -> List[Message]:
        cursor = self.col.find(
            {"user_id": ObjectId(user_id)}
        ).sort("created_at", 1).limit(limit)
        return [self._doc_to_message(d) for d in cursor]
