from datetime import datetime
import hashlib

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def make_user_doc(name: str, password: str) -> dict:
    """Create user document for MongoDB
    
    Args:
        name: Username
        password: Plain password
    
    Returns:
        MongoDB document
    """
    return {
        "name": name,
        "hashed_password": hash_password(password),
        "created_at": datetime.utcnow()
    }

def parse_user_doc(doc: dict) -> dict:
    """Parse MongoDB user document to dict"""
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None
    }

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed_password