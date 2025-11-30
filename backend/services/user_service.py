from datasources.mongodb import get_user_collection
from models.user_model import make_user_doc, parse_user_doc, verify_password
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

def     create_user(name: str, password: str) -> str:
    """Create new user
    
    Args:
        name: Username
        password: Plain password
    
    Returns:
        user_id: Created user ID
    
    Raises:
        ValueError: If name already exists or invalid input
    """
    if not name or not password:
        raise ValueError("Name and password are required")
    
    if len(name) < 3:
        raise ValueError("Name must be at least 3 characters")
    
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    
    col = get_user_collection()
    
    # Check if name exists
    if col.find_one({"name": name}):
        raise ValueError("Username already exists")
    
    try:
        # Create user
        doc = make_user_doc(name, password)
        result = col.insert_one(doc)
        logger.info(f"User created: {name}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise

def validate_user(name: str, password: str) -> dict:
    """Validate user credentials
    
    Args:
        name: Username
        password: Plain password
    
    Returns:
        user: User information dict
    
    Raises:
        ValueError: If credentials are invalid
    """
    if not name or not password:
        raise ValueError("Name and password are required")
    
    col = get_user_collection()
    
    try:
        doc = col.find_one({"name": name})
        
        if not doc:
            raise ValueError("Invalid username or password")
        
        if not verify_password(password, doc["hashed_password"]):
            raise ValueError("Invalid username or password")
        
        logger.info(f"User validated: {name}")
        return parse_user_doc(doc)
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error validating user: {e}")
        raise ValueError("Authentication error")

def get_user_by_id(user_id: str) -> dict:
    """Get user by ID"""
    try:
        col = get_user_collection()
        doc = col.find_one({"_id": ObjectId(user_id)})
        return parse_user_doc(doc)
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None