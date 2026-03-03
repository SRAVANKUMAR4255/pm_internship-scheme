from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.mentor_login, name='mentor_login'),
    path('logout/', views.mentor_logout, name='mentor_logout'),
    path('dashboard/', views.mentor_dashboard, name='mentor_dashboard'),
    path('create-internship/', views.create_internship, name='create_internship'),
    path('applications/', views.view_applications, name='view_applications'),
    path('applications/update/<int:pk>/', views.update_application, name='update_application'),
    path('create-class/', views.create_class, name='create_class'),
]