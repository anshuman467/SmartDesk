import hashlib
from typing import Optional

import streamlit as st

from database.db import UserRecord, authenticate_user, create_user


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_session() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
        
    # Auto-login check (Persist across refresh)
    if not st.session_state.authenticated:
        saved_email = st.query_params.get("u")
        if saved_email:
            from database.db import get_user_by_email
            user = get_user_by_email(saved_email)
            if user:
                st.session_state.authenticated = True
                st.session_state.current_user = {
                    "id": int(user["id"]),
                    "full_name": str(user["full_name"]),
                    "email": str(user["email"]),
                }


def current_user() -> Optional[UserRecord]:
    user = st.session_state.get("current_user")
    return user if isinstance(user, dict) else None


def login(email: str, password: str) -> bool:
    user = authenticate_user(email, hash_password(password))
    if not user:
        return False
    st.session_state.authenticated = True
    st.session_state.current_user = user
    # Set query param for refresh persistence
    st.query_params["u"] = email
    return True


def signup(full_name: str, email: str, password: str) -> tuple[bool, str]:
    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name:
        return False, "Full name is required."
    if "@" not in email or "." not in email:
        return False, "Enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    created = create_user(full_name, email, hash_password(password))
    if not created:
        return False, "An account with this email already exists."

    return True, "Account created successfully. You can log in now."


def logout() -> None:
    st.session_state.authenticated = False
    st.session_state.current_user = None
    # Clear persistence param
    if "u" in st.query_params:
        del st.query_params["u"]


def require_login() -> None:
    init_session()
    if not st.session_state.authenticated:
        st.switch_page("app.py")
