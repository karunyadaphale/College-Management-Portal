"""
Views for Academics Module:
Departments, Courses, Attendance, Examination Marks, and Announcements.
"""

from datetime import datetime, date
from bson.objectid import ObjectId
from django.shortcuts import render, redirect
from django.contrib import messages
from database.mongodb import get_collection
from accounts.decorators import role_required, login_required_mongo
from academics.services import (
    get_all_departments, get_department_by_code, safe_delete_department,
    get_all_courses, get_course_by_code, calculate_attendance_percentage,
    calculate_exam_percentage
)


# ==========================================
# 1. DEPARTMENT MANAGEMENT
# ==========================================

@login_required_mongo
def department_list(request):
    """
    Lists all departments with student and course counts.
    """
    departments = get_all_departments()
    students_col = get_collection('students')
    courses_col = get_collection('courses')

    # Enrich departments with current counts
    for dept in departments:
        dept['student_count'] = students_col.count_documents({"department": dept.get('name')})
        dept['course_count'] = courses_col.count_documents({"department": dept.get('name')})

    return render(request, 'academics/departments.html', {
        'departments': departments
    })


@role_required(['admin'])
def department_add(request):
    """
    Adds a new academic department.
    """
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        name = request.POST.get('name', '').strip()
        hod = request.POST.get('hod', '').strip()
        est_year = request.POST.get('established_year', '').strip()
        description = request.POST.get('description', '').strip()

        if not code or not name:
            messages.error(request, "Department Code and Name are mandatory.")
            return redirect('academics:department_list')

        dept_col = get_collection('departments')
        if dept_col.find_one({"code": code}):
            messages.error(request, f"Department with code '{code}' already exists.")
            return redirect('academics:department_list')

        dept_col.insert_one({
            "code": code,
            "name": name,
            "hod": hod,
            "established_year": int(est_year) if est_year.isdigit() else datetime.now().year,
            "description": description,
            "created_at": datetime.now()
        })
        messages.success(request, f"Department '{name}' ({code}) created successfully.")
        return redirect('academics:department_list')

    return redirect('academics:department_list')


@role_required(['admin'])
def department_edit(request, code):
    """
    Updates department details.
    """
    dept = get_department_by_code(code)
    if not dept:
        messages.error(request, f"Department '{code}' not found.")
        return redirect('academics:department_list')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        hod = request.POST.get('hod', '').strip()
        est_year = request.POST.get('established_year', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, "Department name cannot be empty.")
            return render(request, 'academics/department_edit.html', {'dept': dept})

        old_name = dept.get('name')
        dept_col = get_collection('departments')
        dept_col.update_one(
            {"code": code.upper()},
            {"$set": {
                "name": name,
                "hod": hod,
                "established_year": int(est_year) if est_year.isdigit() else dept.get('established_year', 2020),
                "description": description,
                "updated_at": datetime.now()
            }}
        )

        # Sync name across courses and students if changed
        if old_name != name:
            get_collection('courses').update_many({"department": old_name}, {"$set": {"department": name}})
            get_collection('students').update_many({"department": old_name}, {"$set": {"department": name}})
            get_collection('faculty').update_many({"department": old_name}, {"$set": {"department": name}})

        messages.success(request, f"Department '{code}' updated successfully.")
        return redirect('academics:department_list')

    return render(request, 'academics/department_edit.html', {'dept': dept})


@role_required(['admin'])
def department_delete(request, code):
    """
    Safely deletes a department if no students or courses depend on it.
    """
    if request.method == 'POST':
        success, msg = safe_delete_department(code)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('academics:department_list')


# ==========================================
# 2. COURSE MANAGEMENT
# ==========================================

@login_required_mongo
def course_list(request):
    """
    Lists courses with optional department filter.
    """
    dept_filter = request.GET.get('department', '').strip()
    departments = get_all_departments()
    courses = get_all_courses(department=dept_filter if dept_filter else None)

    # Faculty members for assignment dropdown
    faculty_col = get_collection('faculty')
    faculty_members = list(faculty_col.find().sort("name", 1))

    return render(request, 'academics/courses.html', {
        'courses': courses,
        'departments': departments,
        'faculty_members': faculty_members,
        'selected_department': dept_filter,
    })


@role_required(['admin'])
def course_add(request):
    """
    Adds a new course and assigns a faculty member.
    """
    departments = get_all_departments()
    faculty_col = get_collection('faculty')
    faculty_members = list(faculty_col.find().sort("name", 1))

    if request.method == 'POST':
        course_code = request.POST.get('course_code', '').strip().upper()
        name = request.POST.get('name', '').strip()
        department = request.POST.get('department', '').strip()
        semester = request.POST.get('semester', '').strip()
        faculty_id = request.POST.get('faculty_id', '').strip()
        credits_str = request.POST.get('credits', '3').strip()

        if not all([course_code, name, department, semester]):
            messages.error(request, "Course code, name, department, and semester are required.")
            return redirect('academics:course_list')

        courses_col = get_collection('courses')
        if courses_col.find_one({"course_code": course_code}):
            messages.error(request, f"Course code '{course_code}' is already registered.")
            return redirect('academics:course_list')

        # Find faculty name
        faculty_name = "Unassigned"
        if faculty_id:
            fac = faculty_col.find_one({"faculty_id": faculty_id})
            if fac:
                faculty_name = fac.get('name')
                # Append course to faculty assigned_subjects
                faculty_col.update_one(
                    {"faculty_id": faculty_id},
                    {"$addToSet": {"assigned_subjects": course_code}}
                )

        courses_col.insert_one({
            "course_code": course_code,
            "name": name,
            "department": department,
            "semester": int(semester) if semester.isdigit() else 1,
            "faculty_id": faculty_id,
            "faculty_name": faculty_name,
            "credits": int(credits_str) if credits_str.isdigit() else 3,
            "created_at": datetime.now()
        })
        messages.success(request, f"Course '{name}' ({course_code}) added successfully.")
        return redirect('academics:course_list')

    return redirect('academics:course_list')


@role_required(['admin'])
def course_edit(request, course_code):
    """
    Updates course information and faculty assignment.
    """
    course = get_course_by_code(course_code)
    if not course:
        messages.error(request, f"Course '{course_code}' not found.")
        return redirect('academics:course_list')

    departments = get_all_departments()
    faculty_col = get_collection('faculty')
    faculty_members = list(faculty_col.find().sort("name", 1))

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        department = request.POST.get('department', '').strip()
        semester = request.POST.get('semester', '').strip()
        faculty_id = request.POST.get('faculty_id', '').strip()
        credits_str = request.POST.get('credits', '3').strip()

        if not all([name, department, semester]):
            messages.error(request, "Name, department, and semester are required.")
            return render(request, 'academics/course_edit.html', {
                'course': course, 'departments': departments, 'faculty_members': faculty_members
            })

        old_faculty_id = course.get('faculty_id')
        faculty_name = "Unassigned"
        if faculty_id:
            fac = faculty_col.find_one({"faculty_id": faculty_id})
            if fac:
                faculty_name = fac.get('name')
                faculty_col.update_one({"faculty_id": faculty_id}, {"$addToSet": {"assigned_subjects": course_code}})

        if old_faculty_id and old_faculty_id != faculty_id:
            faculty_col.update_one({"faculty_id": old_faculty_id}, {"$pull": {"assigned_subjects": course_code}})

        courses_col = get_collection('courses')
        courses_col.update_one(
            {"course_code": course_code.upper()},
            {"$set": {
                "name": name,
                "department": department,
                "semester": int(semester) if semester.isdigit() else 1,
                "faculty_id": faculty_id,
                "faculty_name": faculty_name,
                "credits": int(credits_str) if credits_str.isdigit() else 3,
                "updated_at": datetime.now()
            }}
        )
        messages.success(request, f"Course '{course_code}' updated successfully.")
        return redirect('academics:course_list')

    return render(request, 'academics/course_edit.html', {
        'course': course, 'departments': departments, 'faculty_members': faculty_members
    })


@role_required(['admin'])
def course_delete(request, course_code):
    """
    Deletes a course and checks related attendance/marks safety.
    """
    course = get_course_by_code(course_code)
    if not course:
        messages.error(request, f"Course '{course_code}' not found.")
        return redirect('academics:course_list')

    if request.method == 'POST':
        courses_col = get_collection('courses')
        courses_col.delete_one({"course_code": course_code.upper()})

        # Remove from faculty assigned_subjects
        get_collection('faculty').update_many(
            {"assigned_subjects": course_code.upper()},
            {"$pull": {"assigned_subjects": course_code.upper()}}
        )

        messages.success(request, f"Course '{course.get('name')}' ({course_code}) deleted.")
    return redirect('academics:course_list')


# ==========================================
# 3. ATTENDANCE MANAGEMENT
# ==========================================

@role_required(['admin', 'faculty'])
def attendance_mark(request):
    """
    Marks or updates attendance for a specific class date:
    - Step 1: Select Course and Date.
    - Step 2: Lists students enrolled in the course's department & semester.
    - Step 3: Present / Absent radio buttons (with existing status pre-checked if previously marked).
    - Step 4: MongoDB upsert prevents duplicates while allowing updates!
    """
    courses_col = get_collection('courses')
    students_col = get_collection('students')
    attendance_col = get_collection('attendance')

    user_role = request.session.get('role')
    profile_id = request.session.get('profile_id')

    # If faculty, restrict course selection to their assigned courses
    if user_role == 'faculty':
        courses = list(courses_col.find({"faculty_id": profile_id}).sort("course_code", 1))
    else:
        courses = list(courses_col.find().sort("course_code", 1))

    selected_course_code = request.GET.get('course_id', '') or request.POST.get('course_id', '')
    selected_date = request.GET.get('date', '') or request.POST.get('date', date.today().isoformat())

    selected_course = None
    enrolled_students = []

    if selected_course_code:
        selected_course = courses_col.find_one({"course_code": selected_course_code})
        if selected_course:
            # Find students matching course department and semester
            dept = selected_course.get('department')
            sem = selected_course.get('semester')
            enrolled_students = list(students_col.find({
                "department": dept,
                "semester": int(sem)
            }).sort("roll_no", 1))

            # Fetch any previously recorded attendance for this course and date
            existing_records = list(attendance_col.find({
                "course_id": selected_course_code,
                "date": selected_date
            }))
            status_map = {r['student_id']: r['status'] for r in existing_records}

            # Attach status to each student for pre-filling form
            for s in enrolled_students:
                s['attendance_status'] = status_map.get(s['student_id'], 'Present')

    # Handle Attendance Submission
    if request.method == 'POST' and 'submit_attendance' in request.POST:
        if not selected_course:
            messages.error(request, "Please select a valid course first.")
            return redirect('academics:attendance_mark')

        marked_count = 0
        current_user_name = request.session.get('name', 'Faculty')

        for student in enrolled_students:
            s_id = student['student_id']
            status = request.POST.get(f'status_{s_id}', 'Present')

            # Upsert into attendance collection using compound key to prevent duplicates
            filter_query = {
                "student_id": s_id,
                "course_id": selected_course_code,
                "date": selected_date
            }
            update_data = {
                "$set": {
                    "student_id": s_id,
                    "student_name": student.get('name'),
                    "course_id": selected_course_code,
                    "course_name": selected_course.get('name'),
                    "date": selected_date,
                    "status": status,
                    "marked_by": current_user_name,
                    "updated_at": datetime.now()
                }
            }
            attendance_col.update_one(filter_query, update_data, upsert=True)
            marked_count += 1

        messages.success(
            request,
            f"Attendance recorded successfully for {marked_count} students on {selected_date} ({selected_course_code})."
        )
        return redirect(f"{request.path}?course_id={selected_course_code}&date={selected_date}")

    return render(request, 'academics/attendance_mark.html', {
        'courses': courses,
        'selected_course_code': selected_course_code,
        'selected_course': selected_course,
        'selected_date': selected_date,
        'enrolled_students': enrolled_students,
    })


@login_required_mongo
def attendance_view(request):
    """
    Displays attendance history and student percentages.
    - Searchable & filterable by Student, Subject/Course, and Date.
    - Calculates attendance % using formula: (Attended / Total) * 100.
    """
    attendance_col = get_collection('attendance')
    courses_col = get_collection('courses')
    students_col = get_collection('students')

    user_role = request.session.get('role')
    profile_id = request.session.get('profile_id')

    course_filter = request.GET.get('course_id', '').strip()
    student_filter = request.GET.get('student_id', '').strip()
    date_filter = request.GET.get('date', '').strip()

    filters = {}
    if user_role == 'student':
        # Enforce student can ONLY view their own attendance
        filters["student_id"] = profile_id
        student_filter = profile_id
    elif student_filter:
        filters["student_id"] = {"$regex": student_filter, "$options": "i"}

    if course_filter:
        filters["course_id"] = course_filter
    if date_filter:
        filters["date"] = date_filter

    attendance_records = list(attendance_col.find(filters).sort("date", -1).limit(100))

    # Calculate overall summary stats for the current filter
    total_classes = len(attendance_records)
    attended_count = sum(1 for r in attendance_records if r.get('status') == 'Present')
    absent_count = sum(1 for r in attendance_records if r.get('status') == 'Absent')
    pct = calculate_attendance_percentage(attended_count, total_classes)

    courses = list(courses_col.find().sort("course_code", 1))

    return render(request, 'academics/attendance_view.html', {
        'attendance_records': attendance_records,
        'courses': courses,
        'selected_course': course_filter,
        'selected_student': student_filter,
        'selected_date': date_filter,
        'total_classes': total_classes,
        'attended_count': attended_count,
        'absent_count': absent_count,
        'percentage': pct,
    })


# ==========================================
# 4. EXAMINATION & MARKS MANAGEMENT
# ==========================================

@role_required(['admin', 'faculty'])
def marks_entry(request):
    """
    Enters or updates examination marks:
    - Select Course & Exam.
    - Lists students.
    - Validates marks (0 <= marks <= max_marks).
    - Calculates percentage and sets status (Pass >= 40% else Fail).
    - Upserts record to prevent duplicates.
    """
    courses_col = get_collection('courses')
    students_col = get_collection('students')
    exams_col = get_collection('examinations')
    marks_col = get_collection('marks')

    user_role = request.session.get('role')
    profile_id = request.session.get('profile_id')

    if user_role == 'faculty':
        courses = list(courses_col.find({"faculty_id": profile_id}).sort("course_code", 1))
    else:
        courses = list(courses_col.find().sort("course_code", 1))

    examinations = list(exams_col.find().sort("name", 1))

    selected_course_code = request.GET.get('course_id', '') or request.POST.get('course_id', '')
    selected_exam_id = request.GET.get('exam_id', '') or request.POST.get('exam_id', '')
    max_marks_default = float(request.GET.get('max_marks', 100))

    selected_course = None
    selected_exam = None
    enrolled_students = []

    if selected_course_code:
        selected_course = courses_col.find_one({"course_code": selected_course_code})
    if selected_exam_id:
        selected_exam = exams_col.find_one({"exam_id": selected_exam_id})

    if selected_course and selected_exam:
        dept = selected_course.get('department')
        sem = selected_course.get('semester')
        enrolled_students = list(students_col.find({
            "department": dept,
            "semester": int(sem)
        }).sort("roll_no", 1))

        # Check existing marks
        existing_marks = list(marks_col.find({
            "course_id": selected_course_code,
            "exam_id": selected_exam_id
        }))
        marks_map = {m['student_id']: m for m in existing_marks}

        for s in enrolled_students:
            rec = marks_map.get(s['student_id'])
            if rec:
                s['marks_obtained'] = rec.get('marks_obtained', 0)
                s['max_marks'] = rec.get('maximum_marks', max_marks_default)
                s['percentage'] = rec.get('percentage', 0)
                s['pass_status'] = rec.get('status', 'Pass')
            else:
                s['marks_obtained'] = ''
                s['max_marks'] = max_marks_default
                s['percentage'] = ''
                s['pass_status'] = ''

    # Handle Submission
    if request.method == 'POST' and 'submit_marks' in request.POST:
        if not selected_course or not selected_exam:
            messages.error(request, "Please select both course and examination.")
            return redirect('academics:marks_entry')

        updated_count = 0
        for student in enrolled_students:
            s_id = student['student_id']
            marks_input = request.POST.get(f'marks_{s_id}', '').strip()
            max_input = request.POST.get(f'max_{s_id}', str(max_marks_default)).strip()

            if marks_input != '':
                try:
                    obtained = float(marks_input)
                    max_marks = float(max_input)

                    # Validation
                    if obtained < 0:
                        messages.error(request, f"Marks cannot be negative for student {s_id}.")
                        continue
                    if obtained > max_marks:
                        messages.error(request, f"Marks ({obtained}) cannot exceed maximum marks ({max_marks}) for {s_id}.")
                        continue

                    percentage = calculate_exam_percentage(obtained, max_marks)
                    pass_status = "Pass" if percentage >= 40.0 else "Fail"

                    # Upsert
                    marks_col.update_one(
                        {"student_id": s_id, "course_id": selected_course_code, "exam_id": selected_exam_id},
                        {"$set": {
                            "student_id": s_id,
                            "student_name": student.get('name'),
                            "course_id": selected_course_code,
                            "subject": selected_course.get('name'),
                            "exam_id": selected_exam_id,
                            "examination_name": selected_exam.get('name'),
                            "marks_obtained": obtained,
                            "maximum_marks": max_marks,
                            "percentage": percentage,
                            "status": pass_status,
                            "updated_at": datetime.now()
                        }},
                        upsert=True
                    )
                    updated_count += 1
                except ValueError:
                    messages.error(request, f"Invalid numeric marks entered for student {s_id}.")

        messages.success(request, f"Examination marks successfully recorded for {updated_count} students.")
        return redirect(f"{request.path}?course_id={selected_course_code}&exam_id={selected_exam_id}")

    return render(request, 'academics/marks_entry.html', {
        'courses': courses,
        'examinations': examinations,
        'selected_course_code': selected_course_code,
        'selected_exam_id': selected_exam_id,
        'selected_course': selected_course,
        'selected_exam': selected_exam,
        'enrolled_students': enrolled_students,
        'max_marks_default': max_marks_default,
    })


@login_required_mongo
def marks_view(request):
    """
    Displays examination marks with course, exam, and student filtering.
    """
    marks_col = get_collection('marks')
    courses_col = get_collection('courses')
    exams_col = get_collection('examinations')

    user_role = request.session.get('role')
    profile_id = request.session.get('profile_id')

    course_filter = request.GET.get('course_id', '').strip()
    exam_filter = request.GET.get('exam_id', '').strip()
    student_filter = request.GET.get('student_id', '').strip()

    filters = {}
    if user_role == 'student':
        # Enforce student can ONLY view their own marks
        filters["student_id"] = profile_id
        student_filter = profile_id
    elif student_filter:
        filters["student_id"] = {"$regex": student_filter, "$options": "i"}

    if course_filter:
        filters["course_id"] = course_filter
    if exam_filter:
        filters["exam_id"] = exam_filter

    marks_list = list(marks_col.find(filters).sort("percentage", -1))
    courses = list(courses_col.find().sort("course_code", 1))
    examinations = list(exams_col.find().sort("name", 1))

    # Basic stats
    avg_pct = 0.0
    highest_pct = 0.0
    if marks_list:
        pcts = [m.get('percentage', 0) for m in marks_list]
        avg_pct = round(sum(pcts) / len(pcts), 1)
        highest_pct = max(pcts)

    return render(request, 'academics/marks_view.html', {
        'marks_list': marks_list,
        'courses': courses,
        'examinations': examinations,
        'selected_course': course_filter,
        'selected_exam': exam_filter,
        'selected_student': student_filter,
        'avg_pct': avg_pct,
        'highest_pct': highest_pct,
        'total_records': len(marks_list)
    })


# ==========================================
# 5. ANNOUNCEMENTS MODULE
# ==========================================

@login_required_mongo
def announcements_list(request):
    """
    Displays college announcements.
    Admin can create, edit, delete. Faculty and students can view.
    """
    announcements_col = get_collection('announcements')
    announcements = list(announcements_col.find().sort("created_at", -1))
    for a in announcements:
        a['id_str'] = str(a['_id'])

    return render(request, 'academics/announcements.html', {
        'announcements': announcements
    })


@role_required(['admin'])
def announcement_add(request):
    """
    Admin only: publishes a new college announcement.
    """
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'General').strip()
        pub_date = request.POST.get('publication_date', date.today().isoformat()).strip()

        if not title or not description:
            messages.error(request, "Announcement Title and Description cannot be empty.")
            return redirect('academics:announcements_list')

        announcements_col = get_collection('announcements')
        announcements_col.insert_one({
            "title": title,
            "description": description,
            "category": category,
            "author": request.session.get('name', 'Administrator'),
            "publication_date": pub_date,
            "created_at": datetime.now()
        })
        messages.success(request, f"Announcement '{title}' published successfully.")
    return redirect('academics:announcements_list')


@role_required(['admin'])
def announcement_delete(request, announcement_id):
    """
    Admin only: deletes an announcement.
    """
    if request.method == 'POST':
        announcements_col = get_collection('announcements')
        try:
            announcements_col.delete_one({"_id": ObjectId(announcement_id)})
            messages.success(request, "Announcement removed successfully.")
        except Exception:
            messages.error(request, "Invalid announcement ID.")
    return redirect('academics:announcements_list')
