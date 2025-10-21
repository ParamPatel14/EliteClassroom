from django.db import models
from django.conf import settings

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
