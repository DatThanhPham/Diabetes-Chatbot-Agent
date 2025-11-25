import os
from urllib.parse import quote_plus
from pymongo import MongoClient
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(DOTENV_PATH)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_CLUSTER = os.getenv("DB_CLUSTER")       
DB_NAME = os.getenv("DB_NAME", "DCA_DB")

DB_USER_Q = quote_plus(DB_USER or "")
DB_PASSWORD_Q = quote_plus(DB_PASSWORD or "")

MONGO_URI = (
    f"mongodb+srv://{DB_USER_Q}:{DB_PASSWORD_Q}"
    f"@{DB_CLUSTER}/{DB_NAME}?retryWrites=true&w=majority"
)

client = MongoClient(
    MONGO_URI
)

db = client[DB_NAME]

def get_user_collection():
    return db['USER']

def get_assessment_collection():
    return db["ASSESSMENT"]


def get_message_collection():
    return db["MESSAGE"]

# test
if __name__ == "__main__":
    print("Database:", db.name)
    print("Collections:", db.list_collection_names())
