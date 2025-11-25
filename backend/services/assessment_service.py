from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId

from models import Assessment, PyObjectId


class AssessmentService:
    def __init__(self, assessments_col):
        self.col = assessments_col

    def _doc_to_assessment(self, doc) -> Assessment:
        return Assessment(**doc)

    def get_active_assessment(
        self,
        user_id: PyObjectId,
    ) -> Optional[Assessment]:

        doc = self.col.find_one(
            {
                "user_id": ObjectId(user_id),
                "$or": [
                    {"is_valid": True},
                ],
            },
            sort=[("measured_at", -1)],
        )
        return self._doc_to_assessment(doc) if doc else None

    def create_assessment(
        self,
        user_id: PyObjectId,
        metrics: Dict[str, Any],
        measured_at: Optional[datetime] = None,
        prediction: Optional[Dict[str, Any]] = None,
    ) -> Assessment:
        if measured_at is None:
            measured_at = datetime.utcnow()
        now = datetime.utcnow()

        active = self.get_active_assessment(user_id=user_id)
        if active is not None:
            self.col.update_one(
                {"_id": ObjectId(active.id)},
                {"$set": {"is_valid": False}},
            )

        # tạo assessment mới
        doc = {
            "user_id": ObjectId(user_id),
            "measured_at": measured_at,
            "created_at": now,
            "is_valid": True,
            "metrics": metrics,
            "prediction": prediction,
        }

        result = self.col.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._doc_to_assessment(doc)

    def list_assessments(self, user_id: PyObjectId):
        cursor = self.col.find(
            {"user_id": ObjectId(user_id)}
        ).sort("measured_at", -1)
        return [self._doc_to_assessment(d) for d in cursor]
