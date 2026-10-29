"""
Service functions for Student Management in MongoDB.
"""

from database.mongodb import get_collection


def get_all_students(search_query=None, department=None):
    """
    Retrieves students with optional search filtering by name, student_id, or roll_no.
    """
    students_col = get_collection('students')
    filters = {}

    if search_query:
        query_str = search_query.strip()
        filters["$or"] = [
            {"name": {"$regex": query_str, "$options": "i"}},
            {"student_id": {"$regex": query_str, "$options": "i"}},
            {"roll_no": {"$regex": query_str, "$options": "i"}},
        ]

    if department:
        filters["department"] = department.strip()

    return list(students_col.find(filters).sort("student_id", 1))


def get_student_by_id(student_id):
    """
    Finds a single student by unique student_id.
    """
    students_col = get_collection('students')
    return students_col.find_one({"student_id": student_id.strip()})


def check_student_duplicates(student_id, roll_no, current_student_id=None):
    """
    Checks if student_id or roll_no already exists in the database.
    If current_student_id is given (for update), ignores the current record.
    Returns (has_duplicate, error_message).
    """
    students_col = get_collection('students')

    # Student ID check
    query_id = {"student_id": student_id.strip()}
    if current_student_id:
        query_id["student_id"] = {"$ne": current_student_id}
    if students_col.find_one(query_id):
        return True, f"Student ID '{student_id}' is already registered."

    # Roll Number check
    query_roll = {"roll_no": roll_no.strip()}
    if current_student_id:
        query_roll["student_id"] = {"$ne": current_student_id}
    if students_col.find_one(query_roll):
        return True, f"Roll Number '{roll_no}' is already registered."

    return False, ""
