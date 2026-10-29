"""
Views for Faculty Management Module.
"""

from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from database.mongodb import get_collection
from accounts.decorators import role_required, login_required_mongo
from faculty.services import get_all_faculty, get_faculty_by_id, check_faculty_duplicates


@login_required_mongo
def faculty_list(request):
    """
    Displays the list of all faculty members.
    Accessible to Admin and Faculty (and students can view instructors).
    """
    search_query = request.GET.get('search', '').strip()
    department_filter = request.GET.get('department', '').strip()

    dept_col = get_collection('departments')
    departments = list(dept_col.find().sort("name", 1))

    faculty_members = get_all_faculty(search_query=search_query, department=department_filter)

    return render(request, 'faculty/list.html', {
        'faculty_members': faculty_members,
        'departments': departments,
        'search_query': search_query,
        'selected_department': department_filter,
        'total_count': len(faculty_members),
    })


@login_required_mongo
def faculty_detail(request, faculty_id):
    """
    Displays details for a faculty member and their assigned courses.
    """
    faculty = get_faculty_by_id(faculty_id)
    if not faculty:
        messages.error(request, f"Faculty member with ID '{faculty_id}' not found.")
        return redirect('faculty:list')

    courses_col = get_collection('courses')
    assigned_courses = list(courses_col.find({"faculty_id": faculty_id}))

    return render(request, 'faculty/detail.html', {
        'faculty': faculty,
        'assigned_courses': assigned_courses,
    })


@role_required(['admin'])
def faculty_add(request):
    """
    Adds a new faculty member and provisions their login account.
    """
    dept_col = get_collection('departments')
    courses_col = get_collection('courses')
    departments = list(dept_col.find().sort("name", 1))
    all_courses = list(courses_col.find().sort("course_code", 1))

    if request.method == 'POST':
        faculty_id = request.POST.get('faculty_id', '').strip().upper()
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        department = request.POST.get('department', '').strip()
        designation = request.POST.get('designation', '').strip()
        account_status = request.POST.get('account_status', 'Active').strip()
        phone = request.POST.get('phone', '').strip()
        joining_year = request.POST.get('joining_year', '').strip()
        assigned_subjects = request.POST.getlist('assigned_subjects')
        password = request.POST.get('password', 'Faculty@123').strip()

        if not all([faculty_id, name, email, department, designation]):
            messages.error(request, "Please fill in all mandatory fields.")
            return render(request, 'faculty/add.html', {
                'departments': departments,
                'courses': all_courses,
                'form_data': request.POST
            })

        is_dup, err_msg = check_faculty_duplicates(faculty_id, email)
        if is_dup:
            messages.error(request, err_msg)
            return render(request, 'faculty/add.html', {
                'departments': departments,
                'courses': all_courses,
                'form_data': request.POST
            })

        faculty_col = get_collection('faculty')
        users_col = get_collection('users')

        # Check duplicate email in users collection
        if users_col.find_one({"email": email}):
            messages.error(request, f"Email '{email}' is already registered in the system.")
            return render(request, 'faculty/add.html', {
                'departments': departments,
                'courses': all_courses,
                'form_data': request.POST
            })

        faculty_doc = {
            "faculty_id": faculty_id,
            "name": name,
            "email": email,
            "department": department,
            "designation": designation,
            "assigned_subjects": assigned_subjects,
            "account_status": account_status,
            "phone": phone,
            "joining_year": int(joining_year) if joining_year.isdigit() else datetime.now().year,
            "created_at": datetime.now()
        }
        faculty_col.insert_one(faculty_doc)

        # Update assigned courses to reflect this faculty
        if assigned_subjects:
            courses_col.update_many(
                {"course_code": {"$in": assigned_subjects}},
                {"$set": {"faculty_id": faculty_id, "faculty_name": name}}
            )

        # Provision login user account
        user_doc = {
            "username": faculty_id.lower(),
            "email": email,
            "password": make_password(password),
            "role": "faculty",
            "name": name,
            "profile_id": faculty_id,
            "is_active": (account_status == 'Active'),
            "created_at": datetime.now()
        }
        users_col.insert_one(user_doc)

        messages.success(request, f"Faculty member '{name}' ({faculty_id}) added successfully. Login username: '{faculty_id.lower()}'.")
        return redirect('faculty:list')

    return render(request, 'faculty/add.html', {
        'departments': departments,
        'courses': all_courses
    })


@role_required(['admin'])
def faculty_edit(request, faculty_id):
    """
    Updates faculty details and subject assignments.
    """
    faculty = get_faculty_by_id(faculty_id)
    if not faculty:
        messages.error(request, f"Faculty '{faculty_id}' not found.")
        return redirect('faculty:list')

    dept_col = get_collection('departments')
    courses_col = get_collection('courses')
    departments = list(dept_col.find().sort("name", 1))
    all_courses = list(courses_col.find().sort("course_code", 1))

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        department = request.POST.get('department', '').strip()
        designation = request.POST.get('designation', '').strip()
        account_status = request.POST.get('account_status', 'Active').strip()
        phone = request.POST.get('phone', '').strip()
        joining_year = request.POST.get('joining_year', '').strip()
        assigned_subjects = request.POST.getlist('assigned_subjects')

        if not all([name, email, department, designation]):
            messages.error(request, "Please fill in all mandatory fields.")
            return render(request, 'faculty/edit.html', {
                'faculty': faculty,
                'departments': departments,
                'courses': all_courses
            })

        # Check duplicate email
        is_dup, err_msg = check_faculty_duplicates(faculty_id, email, current_faculty_id=faculty_id)
        if is_dup:
            messages.error(request, err_msg)
            return render(request, 'faculty/edit.html', {
                'faculty': faculty,
                'departments': departments,
                'courses': all_courses
            })

        faculty_col = get_collection('faculty')
        faculty_col.update_one(
            {"faculty_id": faculty_id},
            {"$set": {
                "name": name,
                "email": email,
                "department": department,
                "designation": designation,
                "assigned_subjects": assigned_subjects,
                "account_status": account_status,
                "phone": phone,
                "joining_year": int(joining_year) if joining_year.isdigit() else faculty.get('joining_year', 2020),
                "updated_at": datetime.now()
            }}
        )

        # Update course assignments
        courses_col.update_many(
            {"faculty_id": faculty_id},
            {"$set": {"faculty_id": "", "faculty_name": "Unassigned"}}
        )
        if assigned_subjects:
            courses_col.update_many(
                {"course_code": {"$in": assigned_subjects}},
                {"$set": {"faculty_id": faculty_id, "faculty_name": name}}
            )

        # Sync user account
        users_col = get_collection('users')
        users_col.update_one(
            {"profile_id": faculty_id},
            {"$set": {
                "name": name,
                "email": email,
                "is_active": (account_status == 'Active')
            }}
        )

        messages.success(request, f"Faculty details for '{name}' updated successfully.")
        return redirect('faculty:detail', faculty_id=faculty_id)

    return render(request, 'faculty/edit.html', {
        'faculty': faculty,
        'departments': departments,
        'courses': all_courses
    })


@role_required(['admin'])
def faculty_delete(request, faculty_id):
    """
    Deletes a faculty member with confirmation.
    Safely unassigns their courses and removes user account.
    """
    faculty = get_faculty_by_id(faculty_id)
    if not faculty:
        messages.error(request, f"Faculty '{faculty_id}' not found.")
        return redirect('faculty:list')

    if request.method == 'POST':
        faculty_col = get_collection('faculty')
        users_col = get_collection('users')
        courses_col = get_collection('courses')

        # Unassign faculty from courses
        courses_col.update_many(
            {"faculty_id": faculty_id},
            {"$set": {"faculty_id": "", "faculty_name": "Unassigned"}}
        )

        faculty_col.delete_one({"faculty_id": faculty_id})
        users_col.delete_one({"profile_id": faculty_id})

        messages.success(request, f"Faculty '{faculty.get('name')}' ({faculty_id}) deleted successfully.")
        return redirect('faculty:list')

    return render(request, 'faculty/delete_confirm.html', {'faculty': faculty})
