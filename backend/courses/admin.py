from django.contrib import admin
from .models import Course, Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'level', 'price', 'is_active', 'created_at')
    list_filter = ('level', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'teacher__email')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'progress', 'completed', 'enrolled_on')
    list_filter = ('completed', 'course__level')
    search_fields = ('student__email', 'course__title')
