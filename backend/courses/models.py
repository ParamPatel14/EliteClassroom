from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

User = settings.AUTH_USER_MODEL

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='taught_courses',
        limit_choices_to={'role': 'TEACHER'}
    )
    category = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=50, choices=[
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced')
    ], default='BEGINNER')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    duration_weeks = models.PositiveIntegerField(default=4)

    # Media & resources
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    resources = models.JSONField(default=list, blank=True)

    # Meta information
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.teacher.first_name})"


class Enrollment(models.Model):
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='enrolled_courses',
        limit_choices_to={'role': 'STUDENT'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_on = models.DateTimeField(auto_now_add=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.email} enrolled in {self.course.title}"



class Session(models.Model):
    """Model for booking sessions between students and teachers"""
    
    SESSION_STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    SESSION_TYPE = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
    ]
    
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_sessions',
        limit_choices_to={'role': 'STUDENT'}
    )
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='teacher_sessions',
        limit_choices_to={'role': 'TEACHER'}
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sessions'
    )
    
    # Session details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    session_type = models.CharField(max_length=10, choices=SESSION_TYPE, default='ONLINE')
    
    # Scheduling
    scheduled_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    
    # Location (for offline sessions)
    location = models.CharField(max_length=500, blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    
    # Status and payment
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='PENDING')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)
    
    # Notes and feedback
    student_notes = models.TextField(blank=True, null=True)
    teacher_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    provider_room_id = models.CharField(max_length=128, blank=True, null=True)
    recording_assets = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-scheduled_date', '-start_time']
    
    def __str__(self):
        return f"{self.title} - {self.student.email} with {self.teacher.email}"


class Resource(models.Model):
    """Free learning resources for students"""
    
    RESOURCE_TYPE = [
        ('PDF', 'PDF Document'),
        ('VIDEO', 'Video'),
        ('ARTICLE', 'Article'),
        ('QUIZ', 'Quiz'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE, default='PDF')
    
    # File or link
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    
    # Association
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='course_resources',
        null=True,
        blank=True
    )
    category = models.CharField(max_length=100, blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Metadata
    is_free = models.BooleanField(default=True)
    requires_enrollment = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.resource_type})"


class TeacherRating(models.Model):
    """Student ratings for teachers"""
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_ratings',
        limit_choices_to={'role': 'STUDENT'}
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_ratings',
        limit_choices_to={'role': 'TEACHER'}
    )
    session = models.OneToOneField(
        Session,
        on_delete=models.CASCADE,
        related_name='rating',
        null=True,
        blank=True
    )
    
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'teacher', 'session')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.email} rated {self.teacher.email} - {self.rating}/5"
    

from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class TeacherCredential(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credentials')
    degree = models.CharField(max_length=150)
    institution = models.CharField(max_length=200)
    year = models.PositiveIntegerField(null=True, blank=True)
    certification_name = models.CharField(max_length=200, blank=True, null=True)
    achievement = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='credentials/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_credentials')

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.teacher.email} - {self.degree or self.certification_name}"


class TeacherAvailability(models.Model):
    DAYS = [
        (0, 'Mon'), (1, 'Tue'), (2, 'Wed'), (3, 'Thu'),
        (4, 'Fri'), (5, 'Sat'), (6, 'Sun'),
    ]
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    is_recurring = models.BooleanField(default=True)  # weekly
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.teacher.email} {self.get_day_of_week_display()} {self.start_time}-{self.end_time} ({self.timezone})"


class TeacherAvailabilityException(models.Model):
    """One-off blackout/override windows in teacher’s local timezone."""
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availability_exceptions')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    is_blocked = models.BooleanField(default=True)  # block time by default
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.teacher.email} {self.date} {self.start_time}-{self.end_time} blocked={self.is_blocked}"


class SessionMessage(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)


from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

User = settings.AUTH_USER_MODEL

# ... existing models (Course, Session, etc.)

class DemoLecture(models.Model):
    """Demo lectures for teachers to showcase teaching style"""
    
    APPROVAL_STATUS = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='demo_lectures',
        limit_choices_to={'role': 'TEACHER'}
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demo_lectures'
    )
    
    # Content
    title = models.CharField(max_length=255)
    description = models.TextField()
    subject = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField(default=10)
    
    # Video files
    original_video = models.FileField(upload_to='demos/original/', null=True, blank=True)
    transcoded_video = models.FileField(upload_to='demos/transcoded/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='demos/thumbnails/', null=True, blank=True)
    
    # Metadata
    file_size_mb = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    video_codec = models.CharField(max_length=50, blank=True, null=True)
    video_resolution = models.CharField(max_length=20, blank=True, null=True)  # e.g., "1920x1080"
    
    # Approval workflow
    status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='PENDING')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_demos'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_ratings = models.PositiveIntegerField(default=0)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['status', 'teacher']),
            models.Index(fields=['subject', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.teacher.email} ({self.status})"


class DemoRating(models.Model):
    """Student ratings for demo lectures"""
    
    demo = models.ForeignKey(
        DemoLecture,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='demo_ratings',
        limit_choices_to={'role': 'STUDENT'}
    )
    
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('demo', 'student')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.email} rated {self.demo.title} - {self.rating}/5"


class CourseModule(models.Model):
    """Modules/chapters within a course for step-by-step tracking"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    
    # Content
    content = models.TextField(blank=True, null=True)  # Rich text or markdown
    video_url = models.URLField(blank=True, null=True)
    resources = models.JSONField(default=list, blank=True)  # List of resource links
    
    # Requirements
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    is_mandatory = models.BooleanField(default=True)
    prerequisite_modules = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='unlocks'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = ('course', 'order')
    
    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"


class ModuleProgress(models.Model):
    """Student progress tracking for course modules"""
    
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='module_progress'
    )
    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name='student_progress'
    )
    
    # Progress tracking
    is_started = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Time tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    
    # Assessment
    quiz_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('enrollment', 'module')
        ordering = ['module__order']
    
    def __str__(self):
        return f"{self.enrollment.student.email} - {self.module.title} ({self.completion_percentage}%)"


class LearningRoadmap(models.Model):
    """Personalized learning roadmaps for students"""
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='roadmaps',
        limit_choices_to={'role': 'STUDENT'}
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    goal = models.TextField()  # Student's learning goal
    
    # Timeline
    target_completion_date = models.DateField(null=True, blank=True)
    estimated_hours_per_week = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    
    # Courses in roadmap
    courses = models.ManyToManyField(
        Course,
        through='RoadmapCourse',
        related_name='roadmaps'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.email} - {self.title}"


class RoadmapCourse(models.Model):
    """Through model for ordered courses in a roadmap"""
    
    roadmap = models.ForeignKey(LearningRoadmap, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
        unique_together = ('roadmap', 'course')
    
    def __str__(self):
        return f"{self.roadmap.title} - {self.order}. {self.course.title}"
