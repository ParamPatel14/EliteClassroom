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