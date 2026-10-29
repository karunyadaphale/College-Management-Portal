"""
Views for Student Management Module.
"""

from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from database.mongodb import get_collection
from accounts.decorators import role_required, login_required_mongo
from students.services import get_all_students, get_student_by_id, check_student_duplicates


@login_required_mongo
def student_list(request):
    """
    Displays the list of all students.
    Accessible to Admin and Faculty.
    Supports search by Name, Student ID, or Roll Number, and filter by Department.
    """
    user_role = request.session.get('role')
    if user_role not in ['admin', 'faculty']:
        messages.error(request, "Access restricted to administrators and faculty members.")
        return redirect('accounts:home')

    search_query = request.GET.get('search', '').strip()
    department_filter = request.GET.get('department', '').strip()

    dept_col = get_collection('departments')
    departments = list(dept_col.find().sort("name", 1))

    students = get_all_students(search_query=search_query, department=department_filter)

    return render(request, 'students/list.html', {
        'students': students,
        'departments': departments,
        'search_query': search_query,
        'selected_department': department_filter,
        'total_count': len(students),
    })


@login_required_mongo
def student_detail(request, student_id):
    """
    Displays detailed academic profile for a single student.
    - Admin & Faculty can view any student.
    - Students can only view their own record.
    """
    user_role = request.session.get('role')
    profile_id = request.session.get('profile_id')

    if user_role == 'student' and profile_id != student_id:
        messages.error(request, "Unauthorized access: You can only view your own student record.")
        return redirect('accounts:student_dashboard')

    student = get_student_by_id(student_id)
    if not student:
        messages.error(request, f"Student record with ID '{student_id}' was not found.")
        return redirect('students:list')

    # Get attendance history
    attendance_col = get_collection('attendance')
    attendance_records = list(attendance_col.find({"student_id": student_id}).sort("date", -1))
    total_classes = len(attendance_records)
    attended_classes = sum(1 for r in attendance_records if r.get('status') == 'Present')
    attendance_pct = round((attended_classes / total_classes) * 100, 1) if total_classes > 0 else 0.0

    # Get marks records
    marks_col = get_collection('marks')
    marks_records = list(marks_col.find({"student_id": student_id}))

    return render(request, 'students/detail.html', {
        'student': student,
        'attendance_records': attendance_records,
        'total_classes': total_classes,
        'attended_classes': attended_classes,
        'attendance_pct': attendance_pct,
        'marks_records': marks_records,
    })


@role_required(['admin'])
def student_add(request):
    """
    Adds a new student record to MongoDB.
    Admin-only operation with strict input validation.
    Also provisions a student portal login account with default password.
    """
    dept_col = get_collection('departments')
    departments = list(dept_col.find().sort("name", 1))

    if request.method == 'POST':
        student_id = request.POST.get('student_id', '').strip().upper()
        name = request.POST.get('name', '').strip()
        roll_no = request.POST.get('roll_no', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()
        department = request.POST.get('department', '').strip()
        academic_year = request.POST.get('academic_year', '').strip()
        semester = request.POST.get('semester', '').strip()
        admission_year = request.POST.get('admission_year', '').strip()
        account_status = request.POST.get('account_status', 'Active').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', 'Student@123').strip()

        # Validation
        if not all([student_id, name, roll_no, email, department, semester, admission_year]):
            messages.error(request, "Please fill in all mandatory fields.")
            return render(request, 'students/add.html', {'departments': departments, 'form_data': request.POST})

        try:
            sem_int = int(semester)
            adm_int = int(admission_year)
            if sem_int < 1 or sem_int > 8:
                messages.error(request, "Semester must be a valid number between 1 and 8.")
                return render(request, 'students/add.html', {'departments': departments, 'form_data': request.POST})
        except ValueError:
            messages.error(request, "Semester and Admission Year must be valid numeric values.")
            return render(request, 'students/add.html', {'departments': departments, 'form_data': request.POST})

        # Check duplicates
        is_dup, err_msg = check_student_duplicates(student_id, roll_no)
        if is_dup:
            messages.error(request, err_msg)
            return render(request, 'students/add.html', {'departments': departments, 'form_data': request.POST})

        students_col = get_collection('students')
        users_col = get_collection('users')

        # Check email duplicate in users
        if users_col.find_one({"email": email}):
            messages.error(request, f"Email address '{email}' is already associated with an account.")
            return render(request, 'students/add.html', {'departments': departments, 'form_data': request.POST})

        student_doc = {
            "student_id": student_id,
            "roll_no": roll_no,
            "name": name,
            "email": email,
            "department": department,
            "academic_year": academic_year or f"{adm_int}-{adm_int+1}",
            "semester": sem_int,
            "admission_year": adm_int,
            "account_status": account_status,
            "phone": phone,
            "created_at": datetime.now()
        }

        # Insert student record
        students_col.insert_one(student_doc)

        # Create user account for student portal login
        user_doc = {
            "username": student_id.lower(),
            "email": email,
            "password": make_password(password),
            "role": "student",
            "name": name,
            "profile_id": student_id,
            "is_active": (account_status == 'Active'),
            "created_at": datetime.now()
        }
        users_col.insert_one(user_doc)

        messages.success(request, f"Student '{name}' ({student_id}) has been added successfully. Login username: '{student_id.lower()}'.")
        return redirect('students:list')

    return render(request, 'students/add.html', {'departments': departments})


@role_required(['admin'])
def student_edit(request, student_id):
    """
    Updates an existing student's details.
    """
    student = get_student_by_id(student_id)
    if not student:
        messages.error(request, f"Student '{student_id}' does not exist.")
        return redirect('students:list')

    dept_col = get_collection('departments')
    departments = list(dept_col.find().sort("name", 1))

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        roll_no = request.POST.get('roll_no', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()
        department = request.POST.get('department', '').strip()
        academic_year = request.POST.get('academic_year', '').strip()
        semester = request.POST.get('semester', '').strip()
        admission_year = request.POST.get('admission_year', '').strip()
        account_status = request.POST.get('account_status', 'Active').strip()
        phone = request.POST.get('phone', '').strip()

        if not all([name, roll_no, email, department, semester, admission_year]):
            messages.error(request, "Please fill in all mandatory fields.")
            return render(request, 'students/edit.html', {'student': student, 'departments': departments})

        try:
            sem_int = int(semester)
            adm_int = int(admission_year)
        except ValueError:
            messages.error(request, "Semester and Admission Year must be valid numeric values.")
            return render(request, 'students/edit.html', {'student': student, 'departments': departments})

        # Check duplicates on roll_no
        students_col = get_collection('students')
        existing_roll = students_col.find_one({"roll_no": roll_no, "student_id": {"$ne": student_id}})
        if existing_roll:
            messages.error(request, f"Roll Number '{roll_no}' is already assigned to another student.")
            return render(request, 'students/edit.html', {'student': student, 'departments': departments})

        # Update student document
        students_col.update_one(
            {"student_id": student_id},
            {"$set": {
                "name": name,
                "roll_no": roll_no,
                "email": email,
                "department": department,
                "academic_year": academic_year,
                "semester": sem_int,
                "admission_year": adm_int,
                "account_status": account_status,
                "phone": phone,
                "updated_at": datetime.now()
            }}
        )

        # Sync user account
        users_col = get_collection('users')
        users_col.update_one(
            {"profile_id": student_id},
            {"$set": {
                "name": name,
                "email": email,
                "is_active": (account_status == 'Active')
            }}
        )

        # Sync student name in attendance and marks
        attendance_col = get_collection('attendance')
        attendance_col.update_many({"student_id": student_id}, {"$set": {"student_name": name}})
        marks_col = get_collection('marks')
        marks_col.update_many({"student_id": student_id}, {"$set": {"student_name": name}})

        messages.success(request, f"Student details for '{name}' ({student_id}) updated successfully.")
        return redirect('students:detail', student_id=student_id)

    return render(request, 'students/edit.html', {'student': student, 'departments': departments})


@role_required(['admin'])
def student_delete(request, student_id):
    """
    Deletes a student record with confirmation.
    Cascades removal to user account, attendance, and marks.
    """
    student = get_student_by_id(student_id)
    if not student:
        messages.error(request, f"Student record '{student_id}' not found.")
        return redirect('students:list')

    if request.method == 'POST':
        students_col = get_collection('students')
        users_col = get_collection('users')
        attendance_col = get_collection('attendance')
        marks_col = get_collection('marks')

        students_col.delete_one({"student_id": student_id})
        users_col.delete_one({"profile_id": student_id})
        attendance_col.delete_many({"student_id": student_id})
        marks_col.delete_many({"student_id": student_id})

        messages.success(request, f"Student '{student.get('name')}' ({student_id}) and related records deleted successfully.")
        return redirect('students:list')

    return render(request, 'students/delete_confirm.html', {'student': student})
