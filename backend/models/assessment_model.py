from datetime import datetime

def make_assessment_doc(user_id: str, form_data: dict, prediction_result: dict) -> dict:
    """Create assessment document for MongoDB
    
    Args:
        user_id: User ID string
        form_data: Raw form data from user input
        prediction_result: {
            "risk_score": float,
            "risk_level": str ("low" | "high"),
            "prediction": int (0 | 1),
            "model_version": str
        }
    
    Returns:
        MongoDB document
    """
    return {
        "user_id": user_id,
        "measured_at": datetime.utcnow(),  # Thời điểm đo
        "created_at": datetime.utcnow(),   # Thời điểm tạo record
        "is_valid": True,                   # Mặc định là valid
        "metrics": form_data,               # Lưu toàn bộ metrics (BMI, Age, etc.)
        "prediction": prediction_result     # Kết quả dự đoán
    }

def parse_assessment_doc(doc: dict) -> dict:
    """Parse MongoDB assessment document to dict"""
    if not doc:
        return None
    return {
        "_id": str(doc["_id"]),
        "user_id": doc["user_id"],
        "measured_at": doc.get("measured_at").isoformat() if doc.get("measured_at") else None,
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
        "is_valid": doc.get("is_valid", False),
        "metrics": doc.get("metrics", {}),
        "prediction": doc.get("prediction", {})
    }

def invalidate_previous_assessments(user_id: str):
    """Set is_valid=False for all previous assessments of user
    
    Called when creating new assessment
    """
    from datasources.mongodb import get_assessment_collection
    col = get_assessment_collection()
    col.update_many(
        {"user_id": user_id, "is_valid": True},
        {"$set": {"is_valid": False}}
    )