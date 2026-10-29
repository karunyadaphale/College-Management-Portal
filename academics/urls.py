"""
URL configuration for academics module.
"""

from django.urls import path
from academics import views

app_name = 'academics'

urlpatterns = [
    # Departments
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/<str:code>/edit/', views.department_edit, name='department_edit'),
    path('departments/<str:code>/delete/', views.department_delete, name='department_delete'),

    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_add, name='course_add'),
    path('courses/<str:course_code>/edit/', views.course_edit, name='course_edit'),
    path('courses/<str:course_code>/delete/', views.course_delete, name='course_delete'),

    # Attendance
    path('attendance/mark/', views.attendance_mark, name='attendance_mark'),
    path('attendance/view/', views.attendance_view, name='attendance_view'),

    # Marks & Examination
    path('marks/entry/', views.marks_entry, name='marks_entry'),
    path('marks/view/', views.marks_view, name='marks_view'),

    # Announcements
    path('announcements/', views.announcements_list, name='announcements_list'),
    path('announcements/add/', views.announcement_add, name='announcement_add'),
    path('announcements/<str:announcement_id>/delete/', views.announcement_delete, name='announcement_delete'),
]
