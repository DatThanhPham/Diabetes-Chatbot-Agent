from datetime import datetime

def make_message_doc(assessment_id: str, sender_type: str, content: str, metadata: dict = None) -> dict:
    """Create message document for MongoDB
    
    Args:
        assessment_id: Assessment ID string (can be None for general messages)
        sender_type: 'user' or 'agent'
        content: Message content
        metadata: Optional metadata dict
    
    Returns:
        MongoDB document
    """
    if sender_type not in ['user', 'agent']:
        raise ValueError("sender_type must be 'user' or 'agent'")
    
    doc = {
        "sender_type": sender_type,
        "content": content,
        "created_at": datetime.utcnow(),
        "metadata": metadata or {}
    }
    
    # assessment_id is optional
    if assessment_id:
        doc["assessment_id"] = assessment_id
    
    return doc

def parse_message_doc(doc: dict) -> dict:
    """Parse MongoDB message document to dict"""
    if not doc:
        return None
    return {
        "_id": str(doc["_id"]),
        "assessment_id": doc.get("assessment_id"),  # Can be None
        "sender_type": doc["sender_type"],
        "content": doc["content"],
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
        "metadata": doc.get("metadata", {})
    }