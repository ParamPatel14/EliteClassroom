from django.contrib import admin
from .models import Course, Enrollment, Session, Resource, TeacherRating

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

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'teacher', 'scheduled_date', 'status', 'session_type')
    list_filter = ('status', 'session_type', 'scheduled_date')
    search_fields = ('title', 'student__email', 'teacher__email')

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'course', 'is_free', 'views_count', 'created_at')
    list_filter = ('resource_type', 'is_free', 'requires_enrollment')
    search_fields = ('title', 'description')

@admin.register(TeacherRating)
class TeacherRatingAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('student__email', 'teacher__email')
