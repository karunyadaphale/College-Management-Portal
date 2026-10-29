"""
Authentication and Dashboard Views for College Management Portal.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from database.mongodb import get_collection
from accounts.services import authenticate_user
from accounts.decorators import login_required_mongo, role_required


def home_view(request):
    """
    Public landing page.
    Redirects authenticated users to their corresponding dashboard.
    """
    if request.session.get('user_id'):
        role = request.session.get('role')
        if role == 'admin':
            return redirect('accounts:admin_dashboard')
        elif role == 'faculty':
            return redirect('accounts:faculty_dashboard')
        elif role == 'student':
            return redirect('accounts:student_dashboard')

    # Fetch latest announcements for the public home view
    announcements_col = get_collection('announcements')
    latest_announcements = list(announcements_col.find().sort('created_at', -1).limit(3))

    return render(request, 'home.html', {
        'announcements': latest_announcements
    })


def login_view(request):
    """
    Handles user login.
    Validates credentials and redirects based on user role:
    - admin -> /admin/dashboard/
    - faculty -> /faculty/dashboard/
    - student -> /student/dashboard/
    """
    if request.session.get('user_id'):
        return redirect('accounts:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, 'login.html', {'username': username})

        user = authenticate_user(username, password)
        if user:
            # Setup session
            request.session['user_id'] = str(user['_id'])
            request.session['username'] = user.get('username')
            request.session['role'] = user.get('role')
            request.session['name'] = user.get('name')
            request.session['email'] = user.get('email')
            request.session['profile_id'] = user.get('profile_id', '')

            messages.success(request, f"Welcome back, {user.get('name')}! Logged in as {user.get('role').capitalize()}.")

            # Role-based redirection
            role = user.get('role')
            if role == 'admin':
                return redirect('accounts:admin_dashboard')
            elif role == 'faculty':
                return redirect('accounts:faculty_dashboard')
            elif role == 'student':
                return redirect('accounts:student_dashboard')
            return redirect('accounts:home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, 'login.html', {'username': username})

    return render(request, 'login.html')


def logout_view(request):
    """
    Logs out the user and clears the session.
    """
    request.session.flush()
    messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required_mongo
def profile_view(request):
    """
    Displays the logged-in user's profile information.
    """
    role = request.session.get('role')
    profile_id = request.session.get('profile_id')
    profile_data = {}

    if role == 'student':
        students_col = get_collection('students')
        profile_data = students_col.find_one({"student_id": profile_id}) or {}
    elif role == 'faculty':
        faculty_col = get_collection('faculty')
        profile_data = faculty_col.find_one({"faculty_id": profile_id}) or {}

    return render(request, 'profile.html', {
        'profile_data': profile_data,
        'role': role
    })


@role_required(['admin'])
def admin_dashboard(request):
    """
    Admin Dashboard:
    - Counts for students, faculty, departments, courses
    - System attendance summary
    - Recent announcements
    """
    students_col = get_collection('students')
    faculty_col = get_collection('faculty')
    dept_col = get_collection('departments')
    courses_col = get_collection('courses')
    attendance_col = get_collection('attendance')
    announcements_col = get_collection('announcements')

    total_students = students_col.count_documents({})
    total_faculty = faculty_col.count_documents({})
    total_departments = dept_col.count_documents({})
    total_courses = courses_col.count_documents({})

    # Attendance summary
    total_attendance_records = attendance_col.count_documents({})
    present_count = attendance_col.count_documents({"status": "Present"})
    overall_attendance_pct = 0.0
    if total_attendance_records > 0:
        overall_attendance_pct = round((present_count / total_attendance_records) * 100, 1)

    recent_announcements = list(announcements_col.find().sort('created_at', -1).limit(4))
    recent_students = list(students_col.find().sort('admission_year', -1).limit(5))

    context = {
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_departments': total_departments,
        'total_courses': total_courses,
        'total_attendance_records': total_attendance_records,
        'present_count': present_count,
        'overall_attendance_pct': overall_attendance_pct,
        'recent_announcements': recent_announcements,
        'recent_students': recent_students,
    }
    return render(request, 'admin_dashboard.html', context)


@role_required(['faculty'])
def faculty_dashboard(request):
    """
    Faculty Dashboard:
    - Assigned courses & departments
    - Recent attendance records marked by this faculty
    - Students enrolled in their department
    - Announcements
    """
    faculty_id = request.session.get('profile_id')
    courses_col = get_collection('courses')
    attendance_col = get_collection('attendance')
    students_col = get_collection('students')
    announcements_col = get_collection('announcements')

    assigned_courses = list(courses_col.find({"faculty_id": faculty_id}))
    course_codes = [c['course_code'] for c in assigned_courses]

    # Attendance marked for their courses
    recent_attendance = list(attendance_col.find(
        {"course_id": {"$in": course_codes}}
    ).sort('date', -1).limit(8))

    # Relevant students in the same departments as assigned courses
    departments = list(set([c.get('department') for c in assigned_courses if c.get('department')]))
    assigned_students = list(students_col.find({"department": {"$in": departments}}).limit(10))

    recent_announcements = list(announcements_col.find().sort('created_at', -1).limit(4))

    context = {
        'assigned_courses': assigned_courses,
        'recent_attendance': recent_attendance,
        'assigned_students': assigned_students,
        'recent_announcements': recent_announcements,
        'courses_count': len(assigned_courses),
    }
    return render(request, 'faculty_dashboard.html', context)


@role_required(['student'])
def student_dashboard(request):
    """
    Student Dashboard:
    - Personal student profile details
    - Attendance summary (Total, Attended, Percentage with zero-division safety)
    - Examination Marks list & Total Percentage
    - Enrolled courses based on department & semester
    - College announcements
    """
    student_id = request.session.get('profile_id')
    students_col = get_collection('students')
    attendance_col = get_collection('attendance')
    marks_col = get_collection('marks')
    courses_col = get_collection('courses')
    announcements_col = get_collection('announcements')

    # Student Profile
    student = students_col.find_one({"student_id": student_id}) or {}

    # Attendance Calculation
    # Formula: (Classes Attended / Total Classes Conducted) * 100
    student_attendance_records = list(attendance_col.find({"student_id": student_id}))
    total_classes = len(student_attendance_records)
    attended_classes = sum(1 for r in student_attendance_records if r.get('status') == 'Present')

    attendance_percentage = 0.0
    if total_classes > 0:
        attendance_percentage = round((attended_classes / total_classes) * 100, 1)

    # Subject-wise attendance calculation
    subject_attendance = {}
    for r in student_attendance_records:
        c_id = r.get('course_id')
        c_name = r.get('course_name', c_id)
        if c_id not in subject_attendance:
            subject_attendance[c_id] = {'name': c_name, 'total': 0, 'attended': 0}
        subject_attendance[c_id]['total'] += 1
        if r.get('status') == 'Present':
            subject_attendance[c_id]['attended'] += 1

    subject_attendance_list = []
    for c_id, stats in subject_attendance.items():
        pct = round((stats['attended'] / stats['total']) * 100, 1) if stats['total'] > 0 else 0.0
        subject_attendance_list.append({
            'course_id': c_id,
            'course_name': stats['name'],
            'total': stats['total'],
            'attended': stats['attended'],
            'percentage': pct
        })

    # Marks details
    student_marks = list(marks_col.find({"student_id": student_id}))
    total_marks_obtained = sum(m.get('marks_obtained', 0) for m in student_marks)
    total_max_marks = sum(m.get('maximum_marks', 0) for m in student_marks)
    overall_marks_percentage = 0.0
    if total_max_marks > 0:
        overall_marks_percentage = round((total_marks_obtained / total_max_marks) * 100, 1)

    # Enrolled courses in student's department & semester
    enrolled_courses = []
    if student.get('department') and student.get('semester'):
        enrolled_courses = list(courses_col.find({
            "department": student.get('department'),
            "semester": int(student.get('semester'))
        }))

    recent_announcements = list(announcements_col.find().sort('created_at', -1).limit(4))

    context = {
        'student': student,
        'total_classes': total_classes,
        'attended_classes': attended_classes,
        'attendance_percentage': attendance_percentage,
        'subject_attendance_list': subject_attendance_list,
        'student_marks': student_marks,
        'total_marks_obtained': total_marks_obtained,
        'total_max_marks': total_max_marks,
        'overall_marks_percentage': overall_marks_percentage,
        'enrolled_courses': enrolled_courses,
        'recent_announcements': recent_announcements,
    }
    return render(request, 'student_dashboard.html', context)
