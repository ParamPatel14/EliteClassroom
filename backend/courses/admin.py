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


from django.contrib import admin
from django.utils import timezone
from .models import TeacherCredential, TeacherAvailability, TeacherAvailabilityException
from accounts.models import User, TeacherProfile

@admin.register(TeacherCredential)
class TeacherCredentialAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'degree', 'institution', 'verified', 'submitted_at', 'verified_at')
    list_filter = ('verified', 'submitted_at', 'verified_at')
    search_fields = ('teacher__email', 'degree', 'institution', 'certification_name')

    @admin.action(description="Verify selected credentials")
    def verify_credentials(self, request, queryset):
        for cred in queryset:
            cred.verified = True
            cred.verified_at = timezone.now()
            cred.verified_by = request.user
            cred.save()
        # Mark teacher as verified if at least one credential is verified
        teachers = set(q.teacher for q in queryset)
        for t in teachers:
            if t.role == 'TEACHER' and hasattr(t, 'teacher_profile'):
                t.teacher_profile.is_verified = True
                t.teacher_profile.save()
    actions = ['verify_credentials']

@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'day_of_week', 'start_time', 'end_time', 'timezone', 'is_recurring', 'is_active')
    list_filter = ('day_of_week', 'timezone', 'is_recurring', 'is_active')
    search_fields = ('teacher__email',)

@admin.register(TeacherAvailabilityException)
class TeacherAvailabilityExceptionAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'date', 'start_time', 'end_time', 'is_blocked', 'reason')
    list_filter = ('date', 'is_blocked')
    search_fields = ('teacher__email',)

