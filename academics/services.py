"""
Service functions for Academics module (Departments, Courses, Attendance, Marks, Announcements).
"""

from datetime import datetime
from database.mongodb import get_collection


# --- Department Services ---
def get_all_departments():
    col = get_collection('departments')
    return list(col.find().sort("name", 1))


def get_department_by_code(code):
    col = get_collection('departments')
    return col.find_one({"code": code.strip().upper()})


def safe_delete_department(code):
    """
    Prevents deletion if department has enrolled students or associated courses.
    Returns (success, message).
    """
    code = code.strip().upper()
    dept = get_department_by_code(code)
    if not dept:
        return False, "Department not found."

    dept_name = dept.get('name')
    students_col = get_collection('students')
    courses_col = get_collection('courses')

    student_count = students_col.count_documents({"department": dept_name})
    course_count = courses_col.count_documents({"department": dept_name})

    if student_count > 0:
        return False, f"Cannot delete department: {student_count} student(s) are currently enrolled in it."
    if course_count > 0:
        return False, f"Cannot delete department: {course_count} course(s) are associated with it."

    dept_col = get_collection('departments')
    dept_col.delete_one({"code": code})
    return True, f"Department '{dept_name}' deleted successfully."


# --- Course Services ---
def get_all_courses(department=None):
    col = get_collection('courses')
    filters = {}
    if department:
        filters["department"] = department
    return list(col.find(filters).sort("course_code", 1))


def get_course_by_code(course_code):
    col = get_collection('courses')
    return col.find_one({"course_code": course_code.strip().upper()})


# --- Attendance Services ---
def calculate_attendance_percentage(attended_classes, total_classes):
    """
    Calculates attendance percentage with zero-division safety.
    Formula: (Classes Attended / Total Classes Conducted) * 100
    """
    if total_classes <= 0:
        return 0.0
    return round((attended_classes / total_classes) * 100, 1)


# --- Marks Services ---
def calculate_exam_percentage(marks_obtained, max_marks):
    """
    Calculates examination marks percentage.
    Formula: (Marks Obtained / Maximum Marks) * 100
    """
    if max_marks <= 0:
        return 0.0
    return round((marks_obtained / max_marks) * 100, 1)
