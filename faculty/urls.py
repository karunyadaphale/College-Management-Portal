"""
URL configuration for faculty module.
"""

from django.urls import path
from faculty import views

app_name = 'faculty'

urlpatterns = [
    path('', views.faculty_list, name='list'),
    path('add/', views.faculty_add, name='add'),
    path('<str:faculty_id>/', views.faculty_detail, name='detail'),
    path('<str:faculty_id>/edit/', views.faculty_edit, name='edit'),
    path('<str:faculty_id>/delete/', views.faculty_delete, name='delete'),
]
