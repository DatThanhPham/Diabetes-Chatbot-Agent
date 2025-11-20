# frontend/app.py
import streamlit as st
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
print(BACKEND_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from services.user_service import create_user, validate_user  # type: ignore

st.set_page_config(
    page_title="Diabetes Chatbot Agent",
    page_icon="💉",
    layout="centered",
)

if "user" not in st.session_state:
    st.session_state.user = None


def show_logged_in():
    user = st.session_state.user
    st.success(f"Signed in with username: {user['username']}")
    st.write("User ID:", user["id"])
    st.write("Created at:", user.get("created_at"))

    if st.button("Sign out"):
        st.session_state.user = None
        st.rerun()


def login_page():
    st.header("Sign in")

    if st.session_state.user:
        show_logged_in()
        return

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        if not username or not password:
            st.error("Please enter username and password.")
            return

        try:
            user = validate_user(username, password)
            st.session_state.user = user
            st.success("Sign in successfully!")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Unexpected error: {e}")


def register_page():
    st.header("Sign up")

    with st.form("register_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Re-enter password", type="password")
        submitted = st.form_submit_button("Sign up")

    if submitted:
        if not username or not password or not password2:
            st.error("Please enter the information.")
            return

        if password != password2:
            st.error("The password re-enterd have not matched.")
            return

        try:
            user_id = create_user(username, password)
            st.success(f"Sign up successfully! user_id = {user_id}")
            st.info("Please sign in.")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Unexpected error: {e}")


def main():
    st.title("Diabetes Chatbot Agent")

    page = st.sidebar.radio("Menu", ["Sign in", "Sign up"])

    if page == "Sign in":
        login_page()
    else:
        register_page()


if __name__ == "__main__":
    main()
