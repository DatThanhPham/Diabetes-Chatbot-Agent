from datetime import datetime

def make_user_doc(username: str, hashed_password: str, email: str | None = None):
    return {
        "username": username,
        "hashed_password": hashed_password,
        "created_at": datetime.now(),
    }

def parse_user_doc(doc: dict) -> dict:
    if not doc:
        return None

    return {
        "id": str(doc.get("_id")),
        "username": doc.get("username"),
        "hashed_password": doc.get("hashed_password"),
        "created_at": doc.get("created_at"),
    }
