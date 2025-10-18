from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Custom User model with role-based fields"""
    
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.user_type}"
    
    class Meta:
        ordering = ['-created_at']

class StudentProfile(models.Model):
    """Extended profile for students"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    grade_level = models.CharField(max_length=50, blank=True)
    learning_goals = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    preferred_subjects = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"Student: {self.user.username}"

class TeacherProfile(models.Model):
    """Extended profile for teachers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    bio = models.TextField(blank=True)
    education = models.JSONField(default=list, blank=True)  # List of degrees
    certifications = models.JSONField(default=list, blank=True)
    achievements = models.JSONField(default=list, blank=True)
    experience_years = models.IntegerField(default=0)
    subjects = models.JSONField(default=list, blank=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    location = models.CharField(max_length=100, blank=True)
    teaching_mode = models.CharField(max_length=20, choices=[
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('both', 'Both')
    ], default='online')
    is_approved = models.BooleanField(default=False)
    demo_video = models.FileField(upload_to='demos/', blank=True, null=True)
    
    def __str__(self):
        return f"Teacher: {self.user.username}"
