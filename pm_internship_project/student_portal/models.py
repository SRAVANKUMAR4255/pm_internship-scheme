from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, role='student'):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None):
        user = self.create_user(email, full_name, password, role='admin')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (('student', 'Student'), ('mentor', 'Mentor'), ('admin', 'Admin'))
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class Feedback(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='feedbacks')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.student.full_name}"


class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    internship = models.ForeignKey('mentor_portal.Internship', on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    mentor_feedback = models.TextField(blank=True, null=True)
    status_message = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'internship')

    def __str__(self):
        return f"{self.student.full_name} → {self.internship.title} [{self.status}]"



class PredictionResult(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='predictions')
    resume_filename = models.CharField(max_length=255)
    predicted_category = models.CharField(max_length=150)
    confidence_score = models.FloatField(null=True, blank=True)
    top_categories = models.JSONField(default=list)
    top_jobs = models.JSONField(default=list)
    matched_internships = models.JSONField(default=list)
    words_extracted = models.PositiveIntegerField(default=0)
    raw_text_preview = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} — {self.predicted_category} ({self.created_at.date()})"