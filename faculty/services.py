"""
Service functions for Faculty Management in MongoDB.
"""

from database.mongodb import get_collection


def get_all_faculty(search_query=None, department=None):
    """
    Retrieves faculty members with optional search by name, faculty_id, or department.
    """
    faculty_col = get_collection('faculty')
    filters = {}

    if search_query:
        query_str = search_query.strip()
        filters["$or"] = [
            {"name": {"$regex": query_str, "$options": "i"}},
            {"faculty_id": {"$regex": query_str, "$options": "i"}},
            {"designation": {"$regex": query_str, "$options": "i"}},
        ]

    if department:
        filters["department"] = department.strip()

    return list(faculty_col.find(filters).sort("faculty_id", 1))


def get_faculty_by_id(faculty_id):
    """
    Finds a single faculty member by unique faculty_id.
    """
    faculty_col = get_collection('faculty')
    return faculty_col.find_one({"faculty_id": faculty_id.strip()})


def check_faculty_duplicates(faculty_id, email, current_faculty_id=None):
    """
    Checks if faculty_id or email already exists.
    Returns (has_duplicate, error_message).
    """
    faculty_col = get_collection('faculty')

    query_id = {"faculty_id": faculty_id.strip()}
    if current_faculty_id:
        query_id["faculty_id"] = {"$ne": current_faculty_id}
    if faculty_col.find_one(query_id):
        return True, f"Faculty ID '{faculty_id}' is already registered."

    query_email = {"email": email.strip().lower()}
    if current_faculty_id:
        query_email["faculty_id"] = {"$ne": current_faculty_id}
    if faculty_col.find_one(query_email):
        return True, f"Email address '{email}' is already registered to another faculty member."

    return False, ""
