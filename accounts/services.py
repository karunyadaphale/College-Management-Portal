"""
Service layer for Authentication & User operations in MongoDB.
"""

from datetime import datetime
from bson.objectid import ObjectId
from django.contrib.auth.hashers import make_password, check_password
from database.mongodb import get_collection


def authenticate_user(username_or_email, password):
    """
    Validates user credentials against the MongoDB 'users' collection.
    Supports login via either username or email.
    Uses Django's secure check_password function.
    Returns user dict if valid and active, else None.
    """
    users_col = get_collection('users')
    query = {
        "$or": [
            {"username": username_or_email.strip()},
            {"email": username_or_email.strip().lower()}
        ]
    }
    user = users_col.find_one(query)

    if user and user.get('is_active', True):
        # Verify hashed password securely
        if check_password(password, user.get('password', '')):
            return user
    return None


def get_user_by_id(user_id):
    """
    Retrieves a user document by its MongoDB ObjectId.
    """
    users_col = get_collection('users')
    try:
        return users_col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


def create_user(username, email, password, role, name, profile_id):
    """
    Creates a new user account with hashed password.
    Returns (success, result_or_message).
    """
    users_col = get_collection('users')

    # Check for duplicate username or email
    if users_col.find_one({"username": username.strip()}):
        return False, "Username is already taken."
    if users_col.find_one({"email": email.strip().lower()}):
        return False, "Email address is already registered."

    user_doc = {
        "username": username.strip(),
        "email": email.strip().lower(),
        "password": make_password(password),
        "role": role,
        "name": name.strip(),
        "profile_id": profile_id.strip(),
        "is_active": True,
        "created_at": datetime.now()
    }

    try:
        res = users_col.insert_one(user_doc)
        return True, str(res.inserted_id)
    except Exception as e:
        return False, f"Error creating user: {e}"
