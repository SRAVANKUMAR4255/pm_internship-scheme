from django.db import models
from student_portal.models import CustomUser


class Internship(models.Model):
    MODE_CHOICES = (
        ('remote', 'Remote'),
        ('onsite', 'On-Site'),
        ('hybrid', 'Hybrid'),
    )
    DURATION_CHOICES = (
        ('1', '1 Month'),
        ('2', '2 Months'),
        ('3', '3 Months'),
        ('6', '6 Months'),
        ('12', '12 Months'),
    )
    SECTOR_CHOICES = (
        ('technology', 'Technology & IT'),
        ('finance', 'Finance & Banking'),
        ('marketing', 'Marketing & Sales'),
        ('engineering', 'Engineering & Manufacturing'),
        ('healthcare', 'Healthcare & Pharma'),
        ('education', 'Education & Training'),
        ('legal', 'Legal & Compliance'),
        ('design', 'Design & Creative'),
        ('logistics', 'Logistics & Supply Chain'),
        ('agriculture', 'Agriculture & Rural Development'),
        ('other', 'Other'),
    )
    QUALIFICATION_CHOICES = (
        ('class10', 'Class 10 Pass'),
        ('class12', 'Class 12 Pass'),
        ('iti', 'ITI Certificate'),
        ('diploma', 'Diploma'),
        ('graduate', 'Graduate (Any Stream)'),
        ('btech', 'B.Tech / B.E.'),
        ('bsc', 'B.Sc'),
        ('bcom', 'B.Com'),
        ('ba', 'B.A.'),
        ('bca', 'BCA / BBA'),
        ('postgraduate', 'Post Graduate'),
    )

    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='internships')

    # Basic Info
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, default='Unknown')
    location = models.CharField(max_length=255, default='Not Specified')    
    sector = models.CharField(max_length=50, choices=SECTOR_CHOICES, default='technology')
    description = models.TextField()
    responsibilities = models.TextField(help_text='Key responsibilities of the intern', blank=True)

    # Location & Mode
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='onsite')

    # Duration & Compensation
    duration = models.CharField(max_length=5, choices=DURATION_CHOICES, default='3')
    stipend_amount = models.PositiveIntegerField(default=5000, help_text='Monthly stipend in INR')
    openings = models.PositiveIntegerField(default=1)
    last_date_to_apply = models.DateField(help_text='Last date to apply', null=True, blank=True)

    # Requirements
    skills_required = models.TextField(help_text='Comma-separated skills e.g. Python, Excel, Communication')
    qualification_required = models.CharField(max_length=30, choices=QUALIFICATION_CHOICES, default='graduate')
    eligibility = models.TextField(help_text='Additional eligibility criteria for applicants', blank=True)
    age_min = models.PositiveIntegerField(default=18)
    age_max = models.PositiveIntegerField(default=25)

    # Benefits & Perks
    perks = models.TextField(help_text='Comma-separated perks e.g. Certificate, Letter of Recommendation, PPO', blank=True)
    learning_outcomes = models.TextField(help_text='What interns will learn and gain', blank=True)

    # Contact
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)

    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} — {self.company_name}"

    def get_skills_list(self):
        return [s.strip() for s in self.skills_required.split(',') if s.strip()]

    def get_perks_list(self):
        return [p.strip() for p in self.perks.split(',') if p.strip()]

    def total_applications(self):
        return self.applications.count()

    def pending_applications(self):
        return self.applications.filter(status='pending').count()


class LearnClass(models.Model):
    LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )
    CATEGORY_CHOICES = (
        ('technical', 'Technical Skills'),
        ('softskills', 'Soft Skills & Communication'),
        ('finance', 'Finance & Accounting'),
        ('marketing', 'Marketing & Digital'),
        ('legal', 'Legal & Compliance'),
        ('leadership', 'Leadership & Management'),
        ('domain', 'Domain Knowledge'),
        ('other', 'Other'),
    )
    FORMAT_CHOICES = (
        ('live', 'Live Session'),
        ('recorded', 'Recorded / Self-Paced'),
        ('workshop', 'Workshop'),
        ('webinar', 'Webinar'),
    )

    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='classes')

    # Basic Info
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='technical')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    description = models.TextField()
    what_you_will_learn = models.TextField(help_text='Key learning objectives, comma or line separated', blank=True)

    # Class Details
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='live')
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, default=1.0, help_text='Duration in hours')
    total_sessions = models.PositiveIntegerField(default=1)
    schedule = models.CharField(max_length=255, blank=True, help_text='e.g. Every Saturday 10:00 AM IST')
    language = models.CharField(max_length=100, default='English / Hindi')

    # Requirements
    prerequisites = models.TextField(blank=True, help_text='Prerequisites before joining')
    target_audience = models.TextField(blank=True, help_text='Who should attend this class')
    max_students = models.PositiveIntegerField(default=50)

    # Resources
    resources_link = models.URLField(blank=True, help_text='Link to class materials, Google Drive, YouTube, etc.')
    join_link = models.URLField(blank=True, help_text='Zoom / Meet / Teams link for live sessions')

    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_level_display()})"

    def get_learning_list(self):
        return [l.strip() for l in self.what_you_will_learn.replace('\n', ',').split(',') if l.strip()]
    

class Enrollment(models.Model):
    student    = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments')
    learn_class = models.ForeignKey(LearnClass, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'learn_class')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.full_name} → {self.learn_class.title}"