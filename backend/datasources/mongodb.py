"""
MongoDB Connection Manager
"""
from pymongo import MongoClient
from config import Config
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# Global MongoDB client
_mongo_client = None
_db = None

def get_mongo_client():
    """Get or create MongoDB client (singleton)"""
    global _mongo_client, _db
    
    if _mongo_client is None:
        try:
            # Escape username and password
            username = quote_plus(Config.DB_USER)
            password = quote_plus(Config.DB_PASSWORD)
            
            # Build connection string
            connection_string = (
                f"mongodb+srv://{username}:{password}@"
                f"{Config.DB_CLUSTER}/{Config.DB_NAME}?"
                "retryWrites=true&w=majority"
            )
            
            _mongo_client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
            _db = _mongo_client[Config.DB_NAME]
            
            # Test connection
            _mongo_client.admin.command('ping')
            logger.info(f"✓ Connected to MongoDB: {Config.DB_NAME}")
            
        except Exception as e:
            logger.error(f"MongoDB initialization error: {e}")
            raise
    
    return _mongo_client, _db

def get_db():
    """Get database instance - ADDED THIS FUNCTION"""
    _, db = get_mongo_client()
    return db

def get_user_collection():
    """Get users collection"""
    db = get_db()
    return db['users']

def get_assessment_collection():
    """Get assessments collection"""
    db = get_db()
    return db['assessments']

def get_message_collection():
    """Get messages collection"""
    db = get_db()
    return db['messages']

def test_connection():
    """Test MongoDB connection"""
    try:
        client, _ = get_mongo_client()
        client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}")
        return False