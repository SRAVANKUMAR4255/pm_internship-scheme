from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser


def home(request):
    return render(request, 'student_portal/home.html')


def about(request):
    return render(request, 'student_portal/about.html')


def register(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not full_name or not email or not password:
            messages.error(request, 'All fields are required.')
            return render(request, 'student_portal/register.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'student_portal/register.html')

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'student_portal/register.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'student_portal/register.html')

        CustomUser.objects.create_user(email=email, full_name=full_name, password=password, role='student')
        messages.success(request, 'Registration successful! Please login.')
        return redirect('student_login')

    return render(request, 'student_portal/register.html')


import os
import csv
import json
import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import CustomUser, Feedback, Application, PredictionResult
from mentor_portal.models import Internship, LearnClass


# ─── Auth Views ───────────────────────────────────────────────────────────────

def student_login(request):
    if request.user.is_authenticated and request.user.role == 'student':
        return redirect('student_dashboard')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        user = authenticate(request, email=email, password=password)
        if user and user.role == 'student':
            login(request, user)
            return redirect('student_dashboard')
        messages.error(request, 'Invalid credentials or not a student account.')
    return render(request, 'student_portal/login.html')


def student_register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        if not full_name or not email or not password:
            messages.error(request, 'All fields are required.')
        elif password != confirm:
            messages.error(request, 'Passwords do not match.')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            CustomUser.objects.create_user(email=email, full_name=full_name,
                                           password=password, role='student')
            messages.success(request, 'Registered successfully. Please login.')
            return redirect('student_login')
    return render(request, 'student_portal/register.html')


def student_logout(request):
    logout(request)
    return redirect('student_login')


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required(login_url='/student/login/')
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('student_login')
    total_internships = Internship.objects.filter(is_active=True).count()
    total_classes = LearnClass.objects.filter(is_active=True).count()
    my_applications = Application.objects.filter(student=request.user)
    total_applied = my_applications.count()
    pending = my_applications.filter(status='pending').count()
    approved = my_applications.filter(status='approved').count()
    rejected = my_applications.filter(status='rejected').count()
    recent_apps = my_applications.select_related('internship').order_by('-applied_at')[:3]
    total_predictions = PredictionResult.objects.filter(student=request.user).count()
    return render(request, 'student_portal/dashboard.html', {
        'total_internships': total_internships,
        'total_classes': total_classes,
        'total_applied': total_applied,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'recent_apps': recent_apps,
        'total_predictions': total_predictions,
    })


# ─── Profile ──────────────────────────────────────────────────────────────────

@login_required(login_url='/student/login/')
def my_profile(request):
    if request.user.role != 'student':
        return redirect('student_login')
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        if full_name:
            request.user.full_name = full_name
            request.user.save()
            messages.success(request, 'Profile updated.')
            return redirect('my_profile')
    return render(request, 'student_portal/profile.html')


# ─── Feedback ─────────────────────────────────────────────────────────────────

@login_required(login_url='/student/login/')
def submit_feedback(request):
    if request.user.role != 'student':
        return redirect('student_login')
    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        if msg:
            Feedback.objects.create(student=request.user, message=msg)
            messages.success(request, 'Feedback submitted.')
            return redirect('submit_feedback')
        messages.error(request, 'Feedback cannot be empty.')
    return render(request, 'student_portal/feedback.html')


# ─── Internships ──────────────────────────────────────────────────────────────

@login_required(login_url='/student/login/')
def view_internships(request):
    if request.user.role != 'student':
        return redirect('student_login')
    internships = Internship.objects.filter(is_active=True).order_by('-created_at')
    applied_ids = list(Application.objects.filter(
        student=request.user).values_list('internship_id', flat=True))
    return render(request, 'student_portal/internships.html', {
        'internships': internships,
        'applied_ids': applied_ids,
        'total_internships': internships.count(),
        'total_applied': len(applied_ids),
    })


@login_required(login_url='/student/login/')
def apply_internship(request, pk):
    if request.user.role != 'student':
        return redirect('student_login')
    internship = get_object_or_404(Internship, pk=pk, is_active=True)
    if Application.objects.filter(student=request.user, internship=internship).exists():
        messages.warning(request, 'You have already applied to this internship.')
    else:
        Application.objects.create(student=request.user, internship=internship)
        messages.success(request, f'Application submitted for "{internship.title}".')
    # If came from prediction page, redirect back
    next_url = request.GET.get('next', 'view_internships')
    if next_url == 'prediction':
        return redirect('my_predictions')
    return redirect('view_internships')


@login_required(login_url='/student/login/')
def application_status(request):
    if request.user.role != 'student':
        return redirect('student_login')
    apps = Application.objects.filter(
        student=request.user
    ).select_related('internship', 'internship__mentor').order_by('-applied_at')
    return render(request, 'student_portal/application_status.html', {
        'apps': apps,
        'total': apps.count(),
        'pending': apps.filter(status='pending').count(),
        'approved': apps.filter(status='approved').count(),
        'rejected': apps.filter(status='rejected').count(),
    })


# ─── Learn Classes ────────────────────────────────────────────────────────────

from mentor_portal.models import LearnClass, Enrollment

@login_required(login_url='/student/login/')
def learn_classes(request):
    if request.user.role != 'student':
        return redirect('student_login')
    classes = LearnClass.objects.filter(is_active=True).order_by('-created_at')
    enrolled_ids = set(
        Enrollment.objects.filter(student=request.user).values_list('learn_class_id', flat=True)
    )
    return render(request, 'student_portal/learn_classes.html', {
        'classes': classes,
        'total_classes': classes.count(),
        'enrolled_ids': enrolled_ids,
    })


@login_required(login_url='/student/login/')
def enroll_class(request, class_id):
    if request.user.role != 'student':
        return redirect('student_login')
    if request.method == 'POST':
        cls = get_object_or_404(LearnClass, id=class_id, is_active=True)
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            learn_class=cls,
        )
        if created:
            messages.success(request, f'Successfully enrolled in "{cls.title}"!')
        else:
            messages.info(request, f'You are already enrolled in "{cls.title}".')
    return redirect('learn_classes')


@login_required(login_url='/student/login/')
def my_classes(request):
    if request.user.role != 'student':
        return redirect('student_login')
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('learn_class', 'learn_class__mentor').order_by('-enrolled_at')
    return render(request, 'student_portal/my_classes.html', {
        'enrollments': enrollments,
        'total': enrollments.count(),
    })


# ─── Prediction ───────────────────────────────────────────────────────────────

@login_required(login_url='/student/login/')
def prediction(request):
    if request.user.role != 'student':
        return redirect('student_login')

    from . import prediction_engine as pe

    ml_available = pe.models_available()
    result       = None
    error        = None

    if request.method == 'POST':
        resume_file = request.FILES.get('resume_pdf')

        if not resume_file:
            messages.error(request, 'Please upload a PDF resume.')
        elif not resume_file.name.lower().endswith('.pdf'):
            messages.error(request, 'Only PDF files are accepted.')
        elif resume_file.size > 5 * 1024 * 1024:
            messages.error(request, 'File size must be under 5 MB.')
        else:
            import tempfile
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    for chunk in resume_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                # ── Run full prediction (mirrors notebook exactly) ────────────
                pred = pe.run_prediction(tmp_path)
                pred['resume_filename'] = resume_file.name

                # ── Match live mentor internships ─────────────────────────────
                matched = pe.match_mentor_internships(
                    pred['predicted_category'],
                    pred['clean_preview']
                )
                pred['matched_internships'] = matched

                # ── Applied internship IDs (for Apply/Applied buttons) ────────
                pred['applied_ids'] = list(
                    Application.objects.filter(student=request.user)
                    .values_list('internship_id', flat=True)
                )

                # ── Save to DB ────────────────────────────────────────────────
                saved = PredictionResult.objects.create(
                    student=request.user,
                    resume_filename=resume_file.name,
                    predicted_category=pred['predicted_category'],
                    confidence_score=pred.get('confidence_score'),
                    top_categories=pred.get('top3_categories', []),
                    top_jobs=pred.get('top5_jobs', []),
                    matched_internships=matched,
                    words_extracted=pred.get('words_raw', 0),
                    raw_text_preview=pred.get('clean_preview', ''),
                )
                pred['prediction_id'] = saved.id
                result = pred

            except Exception as e:
                error = str(e)
                messages.error(request, f'Prediction failed: {e}')
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    return render(request, 'student_portal/prediction.html', {
        'ml_available': ml_available,
        'result':       result,
        'error':        error,
    })


# ─── My Predictions History ───────────────────────────────────────────────────

@login_required(login_url='/student/login/')
def my_predictions(request):
    if request.user.role != 'student':
        return redirect('student_login')
    predictions = PredictionResult.objects.filter(student=request.user).order_by('-created_at')
    applied_ids = list(Application.objects.filter(
        student=request.user).values_list('internship_id', flat=True))
    return render(request, 'student_portal/my_predictions.html', {
        'predictions': predictions,
        'total_predictions': predictions.count(),
        'applied_ids': applied_ids,
    })


# ─── Prediction Detail ────────────────────────────────────────────────────────

@login_required(login_url='/student/login/')
def prediction_detail(request, pk):
    if request.user.role != 'student':
        return redirect('student_login')
    pred = get_object_or_404(PredictionResult, pk=pk, student=request.user)
    applied_ids = list(Application.objects.filter(
        student=request.user).values_list('internship_id', flat=True))
    return render(request, 'student_portal/prediction_detail.html', {
        'pred': pred,
        'applied_ids': applied_ids,
    })


# ─── Download Prediction ──────────────────────────────────────────────────────

@login_required(login_url='/student/login/')
def download_prediction(request, pk):
    if request.user.role != 'student':
        return redirect('student_login')
    pred = get_object_or_404(PredictionResult, pk=pk, student=request.user)
    fmt = request.GET.get('format', 'csv')

    if fmt == 'json':
        data = {
            'student': request.user.full_name,
            'email': request.user.email,
            'resume_filename': pred.resume_filename,
            'prediction_date': pred.created_at.strftime('%Y-%m-%d %H:%M'),
            'predicted_category': pred.predicted_category,
            'confidence_score': pred.confidence_score,
            'top_categories': pred.top_categories,
            'top_jobs': pred.top_jobs,
            'matched_internships': pred.matched_internships,
        }
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="prediction_{pk}.json"'
        return response

    # Default: CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="prediction_{pk}.csv"'
    writer = csv.writer(response)

    writer.writerow(['PM Internship Scheme — Resume Prediction Report'])
    writer.writerow([])
    writer.writerow(['Student Name', request.user.full_name])
    writer.writerow(['Email', request.user.email])
    writer.writerow(['Resume File', pred.resume_filename])
    writer.writerow(['Prediction Date', pred.created_at.strftime('%d %B %Y, %H:%M')])
    writer.writerow([])

    writer.writerow(['PREDICTED CATEGORY', pred.predicted_category])
    if pred.confidence_score:
        writer.writerow(['CONFIDENCE SCORE', f'{pred.confidence_score:.1f}%'])
    writer.writerow([])

    if pred.top_categories:
        writer.writerow(['TOP CATEGORY PREDICTIONS'])
        writer.writerow(['Rank', 'Category', 'Score (%)'])
        for i, cat in enumerate(pred.top_categories, 1):
            writer.writerow([i, cat.get('category', ''), cat.get('score', '')])
        writer.writerow([])

    if pred.top_jobs:
        writer.writerow(['TOP MATCHING JOBS FROM DATASET'])
        writer.writerow(['Rank', 'Job Title', 'Category', 'Location', 'Similarity Score'])
        for job in pred.top_jobs:
            writer.writerow([
                job.get('rank', ''),
                job.get('job_title', ''),
                job.get('category', ''),
                job.get('location', ''),
                job.get('similarity_score', ''),
            ])
        writer.writerow([])

    if pred.matched_internships:
        writer.writerow(['MATCHING MENTOR INTERNSHIPS'])
        writer.writerow(['Rank', 'Title', 'Company', 'Sector', 'Location',
                         'Stipend', 'Duration', 'Match Score', 'Mentor'])
        for i, intern in enumerate(pred.matched_internships, 1):
            writer.writerow([
                i,
                intern.get('title', ''),
                intern.get('company_name', ''),
                intern.get('sector', ''),
                intern.get('location', ''),
                f"Rs.{intern.get('stipend_amount', '')}",
                intern.get('duration', ''),
                f"{intern.get('match_score', '')}%",
                intern.get('mentor_name', ''),
            ])

    return response


# ─── Apply from Prediction ────────────────────────────────────────────────────

# @login_required(login_url='/student/login/')
# def apply_from_prediction(request, internship_pk, prediction_pk):
#     if request.user.role != 'student':
#         return redirect('student_login')
#     internship = get_object_or_404(Internship, pk=internship_pk, is_active=True)
#     if Application.objects.filter(student=request.user, internship=internship).exists():
#         messages.warning(request, 'You have already applied to this internship.')
#     else:
#         Application.objects.create(student=request.user, internship=internship)
#         messages.success(request, f'Applied to "{internship.title}" at {internship.company_name}!')
#     return redirect('prediction_detail', pk=prediction_pk)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from student_portal.models import CustomUser, Application, Feedback, PredictionResult
from mentor_portal.models import Internship


# ─── View Internships ────────────────────────────────────────────────────────
@login_required(login_url='/student/login/')
def view_internships(request):
    if request.user.role != 'student':
        return redirect('student_login')

    internships = Internship.objects.filter(is_active=True).select_related('mentor').order_by('-created_at')

    # IDs of internships this student already applied to
    applied_ids = set(
        Application.objects.filter(student=request.user).values_list('internship_id', flat=True)
    )

    return render(request, 'student_portal/internships.html', {
        'internships': internships,
        'total_internships': internships.count(),
        'total_applied': len(applied_ids),
        'applied_ids': applied_ids,
    })


# ─── Apply to Internship ──────────────────────────────────────────────────────
@login_required(login_url='/student/login/')
def apply_internship(request, pk):
    if request.user.role != 'student':
        return redirect('student_login')

    internship = get_object_or_404(Internship, pk=pk, is_active=True)

    # Prevent duplicate applications
    if Application.objects.filter(student=request.user, internship=internship).exists():
        messages.warning(request, f'You have already applied to "{internship.title}".')
        return redirect('view_internships')

    if request.method == 'POST':
        Application.objects.create(
            student=request.user,
            internship=internship,
            status='pending',
        )
        messages.success(request, f'Successfully applied to "{internship.title}"! The mentor will review your application.')
        return redirect('application_status')

    # GET — show confirmation page
    return render(request, 'student_portal/apply_confirm.html', {
        'internship': internship,
    })


# ─── Apply from Prediction Page ───────────────────────────────────────────────
@login_required(login_url='/student/login/')
def apply_from_prediction(request, internship_id, prediction_id):
    if request.user.role != 'student':
        return redirect('student_login')

    internship = get_object_or_404(Internship, pk=internship_id, is_active=True)

    if Application.objects.filter(student=request.user, internship=internship).exists():
        messages.warning(request, f'You have already applied to "{internship.title}".')
        return redirect('prediction_detail', pk=prediction_id)

    Application.objects.create(
        student=request.user,
        internship=internship,
        status='pending',
    )
    messages.success(request, f'Successfully applied to "{internship.title}"!')
    return redirect('application_status')


# ─── Application Status (student sees own applications) ──────────────────────
@login_required(login_url='/student/login/')
def application_status(request):
    if request.user.role != 'student':
        return redirect('student_login')

    applications = Application.objects.filter(
        student=request.user
    ).select_related('internship', 'internship__mentor').order_by('-applied_at')

    total     = applications.count()
    pending   = applications.filter(status='pending').count()
    approved  = applications.filter(status='approved').count()
    rejected  = applications.filter(status='rejected').count()

    return render(request, 'student_portal/application_status.html', {
        'applications': applications,
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
    })


# ─── Submit Feedback ──────────────────────────────────────────────────────────
@login_required(login_url='/student/login/')
def submit_feedback(request):
    if request.user.role != 'student':
        return redirect('student_login')

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if not message:
            messages.error(request, 'Feedback message cannot be empty.')
        else:
            Feedback.objects.create(student=request.user, message=message)
            messages.success(request, 'Thank you! Your feedback has been submitted.')
            return redirect('student_dashboard')

    return render(request, 'student_portal/submit_feedback.html')