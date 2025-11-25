from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field
from .common import MongoBaseModel, PyObjectId

class AssessmentPrediction(MongoBaseModel):
    risk_score: float
    risk_level: str
    model_version: str
    explanation: Optional[str] = None

class Assessment(MongoBaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    measured_at: datetime
    created_at: datetime
    is_valid: bool

    metrics: Dict[str, Any]
    prediction: Optional[AssessmentPrediction] = None
    