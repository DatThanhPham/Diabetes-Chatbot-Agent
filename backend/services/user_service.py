from bson import ObjectId
import bcrypt
from datasources.mongodb import get_user_collection
from models.user_model import make_user_doc, parse_user_doc

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt();
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode('utf-8')
    return bcrypt.checkpw(password = password_byte_enc , hashed_password = hashed_password)

def get_user_by_username(username: str) -> dict | None:
    users_col = get_user_collection();
    return users_col.find_one({"username": username})

def create_user(username: str, password: str) -> str:
    users_col = get_user_collection();
    if get_user_by_username(username):
        raise ValueError("Username is existed")
    hashed_password = hash_password(password);
    user_doc = make_user_doc(username, hashed_password)
    result = users_col.insert_one(user_doc)
    return str(result.inserted_id)

def validate_user(username: str, plain_password: str) -> dict:
    user_doc = get_user_by_username(username)
    if not user_doc:
        raise ValueError("Wrong information")
    hashed_password =  user_doc.get("hashed_password")
    if not hashed_password or not verify_password(plain_password, hashed_password):
        raise ValueError("Wrong information")

    return {
        "id": str(user_doc["_id"]),
        "username": user_doc["username"],
        "created_at": user_doc.get("created_at"),
    }
