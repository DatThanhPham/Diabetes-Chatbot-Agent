from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field
from .common import MongoBaseModel, PyObjectId

class Message(MongoBaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    assessment_id: Optional[PyObjectId] = None
    sender_type: str           # "user" | "agent"
    content: str
    created_at: datetime
    metadata: Dict[str, Any] = {}
