"""
MongoDB Database Connection & Utilities using PyMongo.
Academic Project-Based Learning (PBL) - College Management Portal.

This module provides a centralized connection to MongoDB, collection helpers,
and index creation for unique constraints (e.g. unique Roll Number, Faculty ID).
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# Connection Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'college_management_portal')

_client = None
_db = None


def get_mongo_client():
    """
    Returns a singleton MongoClient instance.
    Configured with a 3-second timeout for beginner-friendly quick failure feedback.
    """
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000
            )
            # Verify connectivity
            _client.admin.command('ping')
        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            _client = None
            raise ConnectionError(
                f"Failed to connect to MongoDB at '{MONGO_URI}'. "
                f"Ensure MongoDB service is running. Error details: {err}"
            )
    return _client


def get_db():
    """
    Returns the MongoDB database instance for the College Management Portal.
    """
    global _db
    if _db is None:
        client = get_mongo_client()
        _db = client[MONGO_DB_NAME]
    return _db


def get_collection(collection_name: str):
    """
    Returns a specific collection from MongoDB.
    Example: get_collection('students')
    """
    db = get_db()
    return db[collection_name]


def init_db_indexes():
    """
    Initializes indexes and unique constraints on collections to protect data integrity:
    - users: unique email, username
    - students: unique student_id, roll_no
    - faculty: unique faculty_id, email
    - departments: unique code
    - courses: unique course_code
    - attendance: compound unique index (student_id, course_id, date) to prevent duplicate entries
    - marks: compound unique index (student_id, course_id, exam_id)
    - announcements: index on created_at for fast descending sort
    """
    try:
        db = get_db()

        # Users collection
        db.users.create_index([("username", ASCENDING)], unique=True)
        db.users.create_index([("email", ASCENDING)], unique=True)

        # Students collection
        db.students.create_index([("student_id", ASCENDING)], unique=True)
        db.students.create_index([("roll_no", ASCENDING)], unique=True)
        db.students.create_index([("name", ASCENDING)])
        db.students.create_index([("department", ASCENDING)])

        # Faculty collection
        db.faculty.create_index([("faculty_id", ASCENDING)], unique=True)
        db.faculty.create_index([("email", ASCENDING)], unique=True)
        db.faculty.create_index([("department", ASCENDING)])

        # Departments collection
        db.departments.create_index([("code", ASCENDING)], unique=True)

        # Courses collection
        db.courses.create_index([("course_code", ASCENDING)], unique=True)
        db.courses.create_index([("department", ASCENDING)])

        # Attendance collection - compound unique index prevents duplicate entries on same date
        db.attendance.create_index(
            [("student_id", ASCENDING), ("course_id", ASCENDING), ("date", ASCENDING)],
            unique=True
        )

        # Marks collection - compound unique index prevents duplicate entry for student+course+exam
        db.marks.create_index(
            [("student_id", ASCENDING), ("course_id", ASCENDING), ("exam_id", ASCENDING)],
            unique=True
        )

        # Announcements collection
        db.announcements.create_index([("created_at", DESCENDING)])

        return True, "Indexes initialized successfully."
    except PyMongoError as e:
        return False, f"Failed to initialize indexes: {e}"


def check_connection():
    """
    Simple health check utility for viva demonstration and system health page.
    """
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        return True, "MongoDB connected successfully"
    except Exception as e:
        return False, str(e)
