"""
Root URL Configuration for College Management Portal.
Academic Project-Based Learning (PBL).
"""

from django.urls import path, include

urlpatterns = [
    # Accounts & Authentication (Login, Logout, Dashboards, Home)
    path('', include('accounts.urls')),

    # Student Management Module
    path('students/', include('students.urls')),

    # Faculty Management Module
    path('faculty/', include('faculty.urls')),

    # Academics Module (Departments, Courses, Attendance, Marks, Announcements)
    path('academics/', include('academics.urls')),
]
