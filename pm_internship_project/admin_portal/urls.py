from django.urls import path
from . import views

urlpatterns = [
    path('admin_login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-mentor/', views.add_mentor, name='add_mentor'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('feedback/', views.view_feedback, name='admin_feedback'),
]