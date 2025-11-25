from datetime import datetime
from typing import Optional
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

from models import User, PyObjectId


class UserService:
    def __init__(self, user_col):
        self.col = user_col

    def _doc_to_user(self, doc) -> User:
        return User(**doc)

    def create_user(self, username: str, password: str) -> User:
        now = datetime.utcnow()
        hashed = generate_password_hash(password)
        doc = {
            "username": username,
            "hashed_password": hashed,
            "created_at": now,
        }
        result = self.col.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._doc_to_user(doc)

    def get_user_by_name(self, username: str) -> Optional[User]:
        doc = self.col.find_one({"username": username})
        return self._doc_to_user(doc) if doc else None

    def get_user_by_id(self, user_id: PyObjectId) -> Optional[User]:
        doc = self.col.find_one({"_id": ObjectId(user_id)})
        return self._doc_to_user(doc) if doc else None

    def verify_password(self, user: User, password: str) -> bool:
        return check_password_hash(user.hashed_password, password)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_name(username)
        if not user:
            return None
        if not self.verify_password(user, password):
            return None
        return user
