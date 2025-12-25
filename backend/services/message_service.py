from datasources.mongodb import get_message_collection
from models.message_model import make_message_doc, parse_message_doc
import logging

logger = logging.getLogger(__name__)

def create_message(assessment_id: str, sender_type: str, content: str, metadata: dict = None) -> dict:
    """Create new message
    
    Args:
        assessment_id: Assessment ID string (can be None)
        sender_type: 'user' or 'agent'
        content: Message content
        metadata: Optional metadata
    
    Returns:
        dict: {'success': bool, 'data': {'id': str}, 'error': str}
    """
    try:
        col = get_message_collection()
        doc = make_message_doc(assessment_id, sender_type, content, metadata)
        result = col.insert_one(doc)
        
        message_id = str(result.inserted_id)
        
        logger.info(f"Message created: sender_type={sender_type}, assessment_id={assessment_id}")
        
        return {
            'success': True,
            'data': {
                'id': message_id,
                'assessment_id': assessment_id,
                'sender_type': sender_type
            }
        }
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_messages_by_assessment(assessment_id: str, limit: int = None) -> list:
    """Get chat history by assessment ID
    
    Args:
        assessment_id: Assessment ID string
        limit: Max number of messages (None = all)
    
    Returns:
        messages: List of message dicts, sorted by timestamp
    """
    try:
        col = get_message_collection()
        cursor = col.find({"assessment_id": assessment_id}).sort("created_at", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return [parse_message_doc(doc) for doc in cursor]
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return []

def get_messages_by_user(user_id: str, limit: int = None) -> list:
    """Get all messages of a user (across all assessments)
    
    Args:
        user_id: User ID string
        limit: Max number of messages
    
    Returns:
        messages: List of message dicts
    """
    try:
        from datasources.mongodb import get_assessment_collection
        
        # Get all assessment IDs of user
        col = get_assessment_collection()
        assessments = col.find({"user_id": user_id}, {"_id": 1})
        assessment_ids = [str(a["_id"]) for a in assessments]
        
        # Get messages for these assessments
        msg_col = get_message_collection()
        cursor = msg_col.find({"assessment_id": {"$in": assessment_ids}}).sort("created_at", -1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return [parse_message_doc(doc) for doc in cursor]
    except Exception as e:
        logger.error(f"Error getting user messages: {e}")
        return []

def delete_messages_by_assessment(assessment_id: str) -> int:
    """Delete all messages of an assessment"""
    try:
        col = get_message_collection()
        result = col.delete_many({"assessment_id": assessment_id})
        logger.info(f"Deleted {result.deleted_count} messages for assessment {assessment_id}")
        return result.deleted_count
    except Exception as e:
        logger.error(f"Error deleting messages: {e}")
        return 0