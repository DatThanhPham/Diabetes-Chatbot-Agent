from datasources.mongodb import db
from services.user_service import create_user, get_user_by_username, validate_user

def try_connection():
    print("Database name:", db.name)
    print("Collections:", db.list_collection_names())
    print("User:", db["USER"])
    
def sign_up(username: str, password: str) -> bool:
    try:
        user_id = create_user(username, password)
        print(f"Register successfully! user_id={user_id}")
        return True
    except ValueError as e:
        print("Register failed:", e)
    except Exception as e:
        print("Unexpected error:", e)
        
def sign_in(username: str, password: str) -> bool:
    try:
        user = validate_user(username, password)
        print("Login successfully")
        print("User: ", user)
    except ValueError as e:
        print("Invalid:", e)
    except Exception as e:
        print("Unexpected error:", e)
            

if __name__ == "__main__":
    # signup("letandat1508","123123")
    # print(get_user_by_username("letandat1508"))
    print(sign_in("letandat1508", "123123"))
