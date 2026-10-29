"""
URL configuration for students module.
"""

from django.urls import path
from students import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='list'),
    path('add/', views.student_add, name='add'),
    path('<str:student_id>/', views.student_detail, name='detail'),
    path('<str:student_id>/edit/', views.student_edit, name='edit'),
    path('<str:student_id>/delete/', views.student_delete, name='delete'),
]
