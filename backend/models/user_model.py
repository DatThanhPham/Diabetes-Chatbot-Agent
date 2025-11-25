from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field
from .common import MongoBaseModel, PyObjectId

# def make_user_doc(username: str, hashed_password: str, email: str | None = None):
#     return {
#         "username": username,
#         "hashed_password": hashed_password,
#         "created_at": datetime.now(),
#     }

# def parse_user_doc(doc: dict) -> dict:
#     if not doc:
#         return None

#     return {
#         "id": str(doc.get("_id")),
#         "username": doc.get("username"),
#         "hashed_password": doc.get("hashed_password"),
#         "created_at": doc.get("created_at"),
#     }

class User(MongoBaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now)

    def parse(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "username": self.username,
            "hashed_password": self.hashed_password,
            "created_at": self.created_at,
        }
