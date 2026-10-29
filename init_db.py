"""
Database Initialization & Seed Script
Academic Project-Based Learning (PBL) - College Management Portal.

Creates collections, sets up unique indexes, and seeds exact realistic demo data:
- 1 Administrator account
- 2 Faculty accounts
- 5 Student records
- 2 Departments
- 3 Courses / Subjects
- 12 Attendance records
- 5 Examination mark records
- 2 College Announcements

Run manually: python init_db.py
"""

import os
import sys
from datetime import datetime
from django.contrib.auth.hashers import make_password

# Ensure Django settings are configured so make_password works
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_portal.settings')
import django
django.setup()

from database.mongodb import get_db, init_db_indexes


def seed_database():
    print("=========================================================")
    print("Initializing College Management Portal MongoDB Database...")
    print("=========================================================")

    db = get_db()

    # Step 1: Initialize Indexes
    success, msg = init_db_indexes()
    if not success:
        print(f"Warning on index creation: {msg}")
    else:
        print("[OK] MongoDB indexes and unique constraints initialized.")

    # Drop existing demo collections to ensure clean repeatable state
    collections = ['users', 'students', 'faculty', 'departments', 'courses', 'attendance', 'examinations', 'marks', 'announcements']
    for col in collections:
        db[col].delete_many({})
    print("[OK] Cleared prior collections for fresh initialization.")

    # Step 2: Seed Departments (2 Departments)
    departments_data = [
        {
            "code": "CSE",
            "name": "Computer Science & Engineering",
            "hod": "Dr. Ramesh Sharma",
            "established_year": 2010,
            "description": "Department of Computer Science & Engineering focusing on Algorithms, AI, and Software Engineering."
        },
        {
            "code": "EEE",
            "name": "Electrical & Electronics Engineering",
            "hod": "Prof. Priya Iyer",
            "established_year": 2012,
            "description": "Department of Electrical and Electronics Engineering focusing on Circuits, Power, and Embedded Systems."
        }
    ]
    db.departments.insert_many(departments_data)
    print(f"[OK] Seeded {len(departments_data)} departments.")

    # Step 3: Seed Courses (3 Courses)
    courses_data = [
        {
            "course_code": "CS101",
            "name": "Data Structures & Algorithms",
            "department": "Computer Science & Engineering",
            "semester": 3,
            "faculty_id": "FAC001",
            "faculty_name": "Dr. Ramesh Sharma",
            "credits": 4
        },
        {
            "course_code": "CS102",
            "name": "Database Management Systems",
            "department": "Computer Science & Engineering",
            "semester": 3,
            "faculty_id": "FAC001",
            "faculty_name": "Dr. Ramesh Sharma",
            "credits": 3
        },
        {
            "course_code": "EE101",
            "name": "Digital Circuits & Logic Design",
            "department": "Electrical & Electronics Engineering",
            "semester": 3,
            "faculty_id": "FAC002",
            "faculty_name": "Prof. Priya Iyer",
            "credits": 4
        }
    ]
    db.courses.insert_many(courses_data)
    print(f"[OK] Seeded {len(courses_data)} courses.")

    # Step 4: Seed Faculty (2 Faculty accounts & user accounts)
    faculty_data = [
        {
            "faculty_id": "FAC001",
            "name": "Dr. Ramesh Sharma",
            "email": "sharma.cs@college.edu",
            "department": "Computer Science & Engineering",
            "designation": "Associate Professor",
            "assigned_subjects": ["CS101", "CS102"],
            "account_status": "Active",
            "phone": "+91 98765 43210",
            "joining_year": 2018
        },
        {
            "faculty_id": "FAC002",
            "name": "Prof. Priya Iyer",
            "email": "priya.ee@college.edu",
            "department": "Electrical & Electronics Engineering",
            "designation": "Assistant Professor",
            "assigned_subjects": ["EE101"],
            "account_status": "Active",
            "phone": "+91 98765 43211",
            "joining_year": 2020
        }
    ]
    db.faculty.insert_many(faculty_data)
    print(f"[OK] Seeded {len(faculty_data)} faculty members.")

    # Step 5: Seed Students (5 Students & user accounts)
    students_data = [
        {
            "student_id": "STU001",
            "roll_no": "CS202401",
            "name": "Aarav Mehta",
            "email": "aarav.mehta@student.college.edu",
            "department": "Computer Science & Engineering",
            "academic_year": "2024-2025",
            "semester": 3,
            "admission_year": 2023,
            "account_status": "Active",
            "phone": "+91 91234 56780"
        },
        {
            "student_id": "STU002",
            "roll_no": "CS202402",
            "name": "Ananya Verma",
            "email": "ananya.verma@student.college.edu",
            "department": "Computer Science & Engineering",
            "academic_year": "2024-2025",
            "semester": 3,
            "admission_year": 2023,
            "account_status": "Active",
            "phone": "+91 91234 56781"
        },
        {
            "student_id": "STU003",
            "roll_no": "CS202403",
            "name": "Rohan Kulkarni",
            "email": "rohan.kulkarni@student.college.edu",
            "department": "Computer Science & Engineering",
            "academic_year": "2024-2025",
            "semester": 3,
            "admission_year": 2023,
            "account_status": "Active",
            "phone": "+91 91234 56782"
        },
        {
            "student_id": "STU004",
            "roll_no": "EE202401",
            "name": "Diya Nair",
            "email": "diya.nair@student.college.edu",
            "department": "Electrical & Electronics Engineering",
            "academic_year": "2024-2025",
            "semester": 3,
            "admission_year": 2023,
            "account_status": "Active",
            "phone": "+91 91234 56783"
        },
        {
            "student_id": "STU005",
            "roll_no": "EE202402",
            "name": "Kabir Sen",
            "email": "kabir.sen@student.college.edu",
            "department": "Electrical & Electronics Engineering",
            "academic_year": "2024-2025",
            "semester": 3,
            "admission_year": 2023,
            "account_status": "Active",
            "phone": "+91 91234 56784"
        }
    ]
    db.students.insert_many(students_data)
    print(f"[OK] Seeded {len(students_data)} students.")

    # Step 6: Seed Users (1 Admin, 2 Faculty, 5 Students) with hashed passwords
    users_data = [
        # Administrator
        {
            "username": "admin",
            "email": "admin@college.edu",
            "password": make_password("Admin@123"),
            "role": "admin",
            "name": "System Administrator",
            "profile_id": "ADM001",
            "is_active": True,
            "created_at": datetime.now()
        },
        # Faculty Users
        {
            "username": "fac001",
            "email": "sharma.cs@college.edu",
            "password": make_password("Faculty@123"),
            "role": "faculty",
            "name": "Dr. Ramesh Sharma",
            "profile_id": "FAC001",
            "is_active": True,
            "created_at": datetime.now()
        },
        {
            "username": "fac002",
            "email": "priya.ee@college.edu",
            "password": make_password("Faculty@123"),
            "role": "faculty",
            "name": "Prof. Priya Iyer",
            "profile_id": "FAC002",
            "is_active": True,
            "created_at": datetime.now()
        },
        # Student Users
        {
            "username": "stu001",
            "email": "aarav.mehta@student.college.edu",
            "password": make_password("Student@123"),
            "role": "student",
            "name": "Aarav Mehta",
            "profile_id": "STU001",
            "is_active": True,
            "created_at": datetime.now()
        },
        {
            "username": "stu002",
            "email": "ananya.verma@student.college.edu",
            "password": make_password("Student@123"),
            "role": "student",
            "name": "Ananya Verma",
            "profile_id": "STU002",
            "is_active": True,
            "created_at": datetime.now()
        },
        {
            "username": "stu003",
            "email": "rohan.kulkarni@student.college.edu",
            "password": make_password("Student@123"),
            "role": "student",
            "name": "Rohan Kulkarni",
            "profile_id": "STU003",
            "is_active": True,
            "created_at": datetime.now()
        },
        {
            "username": "stu004",
            "email": "diya.nair@student.college.edu",
            "password": make_password("Student@123"),
            "role": "student",
            "name": "Diya Nair",
            "profile_id": "STU004",
            "is_active": True,
            "created_at": datetime.now()
        },
        {
            "username": "stu005",
            "email": "kabir.sen@student.college.edu",
            "password": make_password("Student@123"),
            "role": "student",
            "name": "Kabir Sen",
            "profile_id": "STU005",
            "is_active": True,
            "created_at": datetime.now()
        }
    ]
    db.users.insert_many(users_data)
    print(f"[OK] Seeded {len(users_data)} users with secure password hashes.")

    # Step 7: Seed Attendance (12 Attendance records)
    attendance_data = [
        # CS101 - Date 2026-10-01
        {"student_id": "STU001", "student_name": "Aarav Mehta", "course_id": "CS101", "course_name": "Data Structures & Algorithms", "date": "2026-10-01", "status": "Present", "marked_by": "FAC001"},
        {"student_id": "STU002", "student_name": "Ananya Verma", "course_id": "CS101", "course_name": "Data Structures & Algorithms", "date": "2026-10-01", "status": "Present", "marked_by": "FAC001"},
        {"student_id": "STU003", "student_name": "Rohan Kulkarni", "course_id": "CS101", "course_name": "Data Structures & Algorithms", "date": "2026-10-01", "status": "Absent", "marked_by": "FAC001"},
        
        # CS101 - Date 2026-10-02
        {"student_id": "STU001", "student_name": "Aarav Mehta", "course_id": "CS101", "course_name": "Data Structures & Algorithms", "date": "2026-10-02", "status": "Present", "marked_by": "FAC001"},
        {"student_id": "STU002", "student_name": "Ananya Verma", "course_id": "CS101", "course_name": "Data Structures & Algorithms", "date": "2026-10-02", "status": "Present", "marked_by": "FAC001"},
        {"student_id": "STU003", "student_name": "Rohan Kulkarni", "course_id": "CS101", "course_name": "Data Structures & Algorithms", "date": "2026-10-02", "status": "Present", "marked_by": "FAC001"},

        # CS102 - Date 2026-10-03
        {"student_id": "STU001", "student_name": "Aarav Mehta", "course_id": "CS102", "course_name": "Database Management Systems", "date": "2026-10-03", "status": "Present", "marked_by": "FAC001"},
        {"student_id": "STU002", "student_name": "Ananya Verma", "course_id": "CS102", "course_name": "Database Management Systems", "date": "2026-10-03", "status": "Absent", "marked_by": "FAC001"},
        {"student_id": "STU003", "student_name": "Rohan Kulkarni", "course_id": "CS102", "course_name": "Database Management Systems", "date": "2026-10-03", "status": "Present", "marked_by": "FAC001"},

        # EE101 - Date 2026-10-01
        {"student_id": "STU004", "student_name": "Diya Nair", "course_id": "EE101", "course_name": "Digital Circuits & Logic Design", "date": "2026-10-01", "status": "Present", "marked_by": "FAC002"},
        {"student_id": "STU005", "student_name": "Kabir Sen", "course_id": "EE101", "course_name": "Digital Circuits & Logic Design", "date": "2026-10-01", "status": "Present", "marked_by": "FAC002"},

        # EE101 - Date 2026-10-02
        {"student_id": "STU004", "student_name": "Diya Nair", "course_id": "EE101", "course_name": "Digital Circuits & Logic Design", "date": "2026-10-02", "status": "Present", "marked_by": "FAC002"},
    ]
    db.attendance.insert_many(attendance_data)
    print(f"[OK] Seeded {len(attendance_data)} attendance records.")

    # Step 8: Seed Examinations & Marks (5 Examination Marks records)
    examinations_data = [
        {
            "exam_id": "MID2026",
            "name": "Mid-Semester Examination 2026",
            "semester": 3,
            "academic_year": "2024-2025"
        }
    ]
    db.examinations.insert_many(examinations_data)

    marks_data = [
        {
            "student_id": "STU001",
            "student_name": "Aarav Mehta",
            "course_id": "CS101",
            "subject": "Data Structures & Algorithms",
            "exam_id": "MID2026",
            "examination_name": "Mid-Semester Examination 2026",
            "marks_obtained": 85.0,
            "maximum_marks": 100.0,
            "percentage": 85.0,
            "status": "Pass"
        },
        {
            "student_id": "STU002",
            "student_name": "Ananya Verma",
            "course_id": "CS101",
            "subject": "Data Structures & Algorithms",
            "exam_id": "MID2026",
            "examination_name": "Mid-Semester Examination 2026",
            "marks_obtained": 92.0,
            "maximum_marks": 100.0,
            "percentage": 92.0,
            "status": "Pass"
        },
        {
            "student_id": "STU003",
            "student_name": "Rohan Kulkarni",
            "course_id": "CS101",
            "subject": "Data Structures & Algorithms",
            "exam_id": "MID2026",
            "examination_name": "Mid-Semester Examination 2026",
            "marks_obtained": 74.0,
            "maximum_marks": 100.0,
            "percentage": 74.0,
            "status": "Pass"
        },
        {
            "student_id": "STU004",
            "student_name": "Diya Nair",
            "course_id": "EE101",
            "subject": "Digital Circuits & Logic Design",
            "exam_id": "MID2026",
            "examination_name": "Mid-Semester Examination 2026",
            "marks_obtained": 88.0,
            "maximum_marks": 100.0,
            "percentage": 88.0,
            "status": "Pass"
        },
        {
            "student_id": "STU005",
            "student_name": "Kabir Sen",
            "course_id": "EE101",
            "subject": "Digital Circuits & Logic Design",
            "exam_id": "MID2026",
            "examination_name": "Mid-Semester Examination 2026",
            "marks_obtained": 68.0,
            "maximum_marks": 100.0,
            "percentage": 68.0,
            "status": "Pass"
        }
    ]
    db.marks.insert_many(marks_data)
    print(f"[OK] Seeded {len(marks_data)} examination mark records.")

    # Step 9: Seed Announcements (2 Announcements)
    announcements_data = [
        {
            "title": "Mid-Semester Examination Schedule Announced",
            "description": "The Mid-Semester theory and laboratory examinations for Semester 3 will commence on October 25, 2026. Hall tickets and time tables are available on the portal.",
            "author": "System Administrator",
            "category": "Academic",
            "publication_date": "2026-10-05",
            "created_at": datetime.now()
        },
        {
            "title": "Annual Technical Symposium & Project Exhibition",
            "description": "Registrations are now open for the Annual Project Exhibition. Students can submit their project abstracts by October 20. Exciting awards and certificates will be presented.",
            "author": "System Administrator",
            "category": "Events",
            "publication_date": "2026-10-07",
            "created_at": datetime.now()
        }
    ]
    db.announcements.insert_many(announcements_data)
    print(f"[OK] Seeded {len(announcements_data)} college announcements.")

    print("=========================================================")
    print("Database Initialization Completed Successfully!")
    print("=========================================================")
    print("Demo Login Credentials:")
    print("  * Admin:   username='admin'   password='Admin@123'")
    print("  * Faculty: username='fac001'  password='Faculty@123'")
    print("  * Faculty: username='fac002'  password='Faculty@123'")
    print("  * Student: username='stu001'  password='Student@123'")
    print("  * Student: username='stu002'  password='Student@123'")
    print("=========================================================")


if __name__ == "__main__":
    seed_database()
