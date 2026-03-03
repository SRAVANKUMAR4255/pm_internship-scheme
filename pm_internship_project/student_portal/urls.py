from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name='register'),
    path('login/', views.student_login, name='student_login'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.student_logout, name='student_logout'),

    
    path('profile/', views.my_profile, name='my_profile'),
    path('feedback/', views.submit_feedback, name='submit_feedback'),
    path('prediction/', views.prediction, name='prediction'),
    path('internships/', views.view_internships, name='view_internships'),
    path('internships/apply/<int:pk>/', views.apply_internship, name='apply_internship'),
    path('applications/', views.application_status, name='application_status'),
    path('student/classes/',          views.learn_classes, name='learn_classes'),
    path('student/classes/enroll/<int:class_id>/', views.enroll_class, name='enroll_class'),
    path('student/classes/my/',       views.my_classes,    name='my_classes'),    # Prediction
    path('prediction/', views.prediction, name='prediction'),
    path('my-predictions/', views.my_predictions, name='my_predictions'),
    path('my-predictions/<int:pk>/', views.prediction_detail, name='prediction_detail'),
    path('my-predictions/<int:pk>/download/', views.download_prediction, name='download_prediction'),
    path('my-predictions/<int:prediction_pk>/apply/<int:internship_pk>/',
         views.apply_from_prediction, name='apply_from_prediction'),

         # student_portal
    path('student/internships/',                    views.view_internships,      name='view_internships'),
    path('student/internships/apply/<int:pk>/',     views.apply_internship,      name='apply_internship'),
    path('student/internships/apply-from-prediction/<int:internship_id>/<int:prediction_id>/',
                                                    views.apply_from_prediction, name='apply_from_prediction'),
    path('student/applications/',                   views.application_status,    name='application_status'),
    path('student/feedback/',                       views.submit_feedback,       name='submit_feedback'),


]
