from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from student_portal.models import CustomUser


def admin_login(request):
    if request.user.is_authenticated and request.user.role == 'admin':
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Admin logs in via hardcoded username 'admin'
        # We authenticate by finding the admin user
        try:
            admin_user = CustomUser.objects.get(email='admin@pm-internship.gov.in', role='admin')
            if username == 'admin' and admin_user.check_password(password):
                login(request, admin_user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid admin credentials.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Admin account not set up. Run setup_admin command.')

    return render(request, 'admin_portal/login.html')


@login_required(login_url='/admin-portal/login/')
def admin_dashboard(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('admin_login')

    students = CustomUser.objects.filter(role='student')
    mentors = CustomUser.objects.filter(role='mentor')
    total_students = students.count()
    total_mentors = mentors.count()

    context = {
        'total_students': total_students,
        'total_mentors': total_mentors,
        'students': students,
        'mentors': mentors,
    }
    return render(request, 'admin_portal/dashboard.html', context)


@login_required(login_url='/admin-portal/login/')
def add_mentor(request):
    if request.user.role != 'admin':
        return redirect('admin_login')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not full_name or not email or not password:
            messages.error(request, 'All fields are required.')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
        else:
            CustomUser.objects.create_user(email=email, full_name=full_name, password=password, role='mentor')
            messages.success(request, f'Mentor "{full_name}" added successfully.')
            return redirect('admin_dashboard')

    return render(request, 'admin_portal/add_mentor.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from student_portal.models import CustomUser, Feedback



@login_required(login_url='/admin-portal/login/')
def view_feedback(request):
    if request.user.role != 'admin':
        return redirect('admin_login')
    feedbacks = Feedback.objects.filter(student__role='student').select_related('student').order_by('-created_at')
    return render(request, 'admin_portal/feedback.html', {'feedbacks': feedbacks})