from datasources.mongodb import get_assessment_collection
from models.assessment_model import make_assessment_doc, parse_assessment_doc, invalidate_previous_assessments
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

def create_assessment(user_id: str, form_data: dict, prediction: int) -> str:
    """Create new assessment and invalidate previous ones
    
    Args:
        user_id: User ID string
        form_data: Form data dictionary (metrics)
        prediction: Prediction result (0 or 1)
    
    Returns:
        assessment_id: Created assessment ID
    """
    try:
        # Invalidate previous assessments (Business Rule)
        invalidate_previous_assessments(user_id)
        
        # Build prediction document
        prediction_result = {
            "prediction": prediction,
            "risk_level": "high" if prediction == 1 else "low",
            "risk_score": float(prediction),  # You can enhance this later
            "model_version": "v1.0"
        }
        
        # Create new assessment
        col = get_assessment_collection()
        doc = make_assessment_doc(user_id, form_data, prediction_result)
        result = col.insert_one(doc)
        
        logger.info(f"Assessment created for user {user_id}: prediction={prediction}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error creating assessment: {e}")
        raise

def get_assessments_by_user(user_id: str, valid_only: bool = False) -> list:
    """Get assessments of a user
    
    Args:
        user_id: User ID string
        valid_only: If True, only return valid assessments
    
    Returns:
        assessments: List of assessment dicts, sorted by newest first
    """
    try:
        col = get_assessment_collection()
        
        query = {"user_id": user_id}
        if valid_only:
            query["is_valid"] = True
        
        cursor = col.find(query).sort("created_at", -1)
        return [parse_assessment_doc(doc) for doc in cursor]
    except Exception as e:
        logger.error(f"Error getting assessments: {e}")
        return []

def get_assessment_by_id(assessment_id: str) -> dict:
    """Get assessment by ID"""
    try:
        col = get_assessment_collection()
        doc = col.find_one({"_id": ObjectId(assessment_id)})
        return parse_assessment_doc(doc) if doc else None
    except Exception as e:
        logger.error(f"Error getting assessment by ID: {e}")
        return None

def get_latest_valid_assessment(user_id: str) -> dict:
    """Get latest VALID assessment of user (Business Rule)
    
    Args:
        user_id: User ID string
    
    Returns:
        assessment: Latest valid assessment dict or None
    """
    try:
        col = get_assessment_collection()
        doc = col.find_one(
            {"user_id": user_id, "is_valid": True},
            sort=[("created_at", -1)]
        )
        return parse_assessment_doc(doc) if doc else None
    except Exception as e:
        logger.error(f"Error getting latest valid assessment: {e}")
        return None

def get_latest_assessment(user_id: str) -> dict:
    """Get latest assessment (regardless of validity)"""
    try:
        col = get_assessment_collection()
        doc = col.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )
        return parse_assessment_doc(doc) if doc else None
    except Exception as e:
        logger.error(f"Error getting latest assessment: {e}")
        return None