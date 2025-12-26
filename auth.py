import json
import os
import hashlib
import secrets
from typing import Dict, Optional, Tuple
import streamlit as st

# Constants
TEACHERS_FILE = "teachers.json"
SALT_LENGTH = 32

def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """Hash a password with salt using SHA-256"""
    if salt is None:
        salt = secrets.token_hex(SALT_LENGTH)
    salted_password = password + salt
    hashed = hashlib.sha256(salted_password.encode()).hexdigest()
    return hashed, salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify a password against its hash and salt"""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == hashed

def init_teachers_file() -> None:
    """Initialize the teachers data file if it doesn't exist"""
    if not os.path.exists(TEACHERS_FILE):
        with open(TEACHERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def load_teachers() -> list:
    """Load teachers from JSON file"""
    init_teachers_file()
    try:
        with open(TEACHERS_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_teachers(teachers: list) -> None:
    """Save teachers to JSON file"""
    with open(TEACHERS_FILE, "w", encoding='utf-8') as f:
        json.dump(teachers, f, indent=4)

def register_teacher(email: str, password: str, name: str) -> Tuple[bool, str]:
    """
    Register a new teacher
    Returns: (success: bool, message: str)
    """
    teachers = load_teachers()

    # Check if email already exists
    if any(t['email'] == email for t in teachers):
        return False, "Email already registered"

    # Validate input
    if not email.strip() or not password.strip() or not name.strip():
        return False, "All fields are required"

    if len(password) < 6:
        return False, "Password must be at least 6 characters long"

    # Hash password
    hashed_password, salt = hash_password(password)

    # Create teacher record
    teacher = {
        "email": email.strip(),
        "password_hash": hashed_password,
        "salt": salt,
        "name": name.strip(),
        "created_at": str(pd.Timestamp.now()) if 'pd' in globals() else str(__import__('datetime').datetime.now())
    }

    teachers.append(teacher)
    save_teachers(teachers)

    return True, "Registration successful! Please login."

def login_teacher(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Login a teacher
    Returns: (success: bool, message: str, teacher_data: dict or None)
    """
    teachers = load_teachers()

    # Find teacher by email
    teacher = next((t for t in teachers if t['email'] == email), None)

    if not teacher:
        return False, "Email not found", None

    # Verify password
    if not verify_password(password, teacher['password_hash'], teacher['salt']):
        return False, "Invalid password", None

    # Return teacher data (excluding sensitive info)
    teacher_data = {
        "email": teacher["email"],
        "name": teacher["name"],
        "created_at": teacher["created_at"]
    }

    return True, "Login successful", teacher_data

def init_auth_session_state() -> None:
    """Initialize authentication-related session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'teacher_data' not in st.session_state:
        st.session_state.teacher_data = None
    if 'auth_page' not in st.session_state:
        st.session_state.auth_page = "login"  # "login" or "register"

def logout() -> None:
    """Logout the current teacher"""
    st.session_state.authenticated = False
    st.session_state.teacher_data = None
    st.session_state.auth_page = "login"

def require_auth() -> bool:
    """Check if user is authenticated, redirect to login if not"""
    if not st.session_state.authenticated:
        show_auth_page()
        return False
    return True

def show_auth_page() -> None:
    """Display the authentication page (login/register)"""
    st.set_page_config(
        page_title="SMIS - Teacher Login",
        page_icon="🎓",
        layout="centered"
    )

    # Custom CSS for auth page
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: #f8f9fa;
    }
    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
        color: #1E3A8A;
    }
    .auth-tabs {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    .auth-tab {
        padding: 0.5rem 1rem;
        margin: 0 0.5rem;
        border-radius: 5px;
        cursor: pointer;
        background-color: #e9ecef;
        border: none;
    }
    .auth-tab.active {
        background-color: #1E3A8A;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='auth-header'>🎓 Student Management Information System</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-bottom: 2rem;'>Teacher Portal</h3>", unsafe_allow_html=True)

    # Tab selection
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Login", use_container_width=True, type="primary" if st.session_state.auth_page == "login" else "secondary"):
            st.session_state.auth_page = "login"
            st.rerun()
    with col2:
        if st.button("📝 Register", use_container_width=True, type="primary" if st.session_state.auth_page == "register" else "secondary"):
            st.session_state.auth_page = "register"
            st.rerun()

    st.divider()

    if st.session_state.auth_page == "login":
        show_login_form()
    else:
        show_register_form()

def show_login_form() -> None:
    """Display the login form"""
    st.subheader("🔐 Teacher Login")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please fill in all fields")
            else:
                success, message, teacher_data = login_teacher(email, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.teacher_data = teacher_data
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

def show_register_form() -> None:
    """Display the registration form"""
    st.subheader("📝 Teacher Registration")

    with st.form("register_form"):
        name = st.text_input("Full Name", placeholder="Enter your full name")
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Create a password (min 6 characters)")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")

        submitted = st.form_submit_button("Register", type="primary", use_container_width=True)

        if submitted:
            if not name or not email or not password or not confirm_password:
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                success, message = register_teacher(email, password, name)
                if success:
                    st.success(message)
                    st.session_state.auth_page = "login"
                    st.rerun()
                else:
                    st.error(message)
