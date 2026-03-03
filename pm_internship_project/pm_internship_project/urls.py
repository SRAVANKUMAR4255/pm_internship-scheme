from django.urls import path, include
from django.shortcuts import redirect

def root_redirect(request):
    return redirect('/student/')

urlpatterns = [
    path('', root_redirect),
    path('student/', include('student_portal.urls')),
    path('mentor/', include('mentor_portal.urls')),
    path('admin-portal/', include('admin_portal.urls')),
]
