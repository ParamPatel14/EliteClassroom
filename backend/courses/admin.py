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

from django.contrib import admin
from django.utils import timezone
from django.db.models import Avg
from .models import (
    Course, Enrollment, Session, Resource, TeacherRating,
    TeacherCredential, TeacherAvailability, TeacherAvailabilityException,
    DemoLecture, DemoRating, CourseModule, ModuleProgress, 
    LearningRoadmap, RoadmapCourse
)

# ... existing admin classes

@admin.register(DemoLecture)
class DemoLectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'subject', 'status', 'average_rating', 'view_count', 'uploaded_at')
    list_filter = ('status', 'subject', 'uploaded_at')
    search_fields = ('title', 'teacher__email', 'subject', 'description')
    readonly_fields = ('view_count', 'average_rating', 'total_ratings', 'uploaded_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('teacher', 'course', 'title', 'description', 'subject', 'duration_minutes')
        }),
        ('Video Files', {
            'fields': ('original_video', 'transcoded_video', 'thumbnail', 'file_size_mb', 
                      'video_codec', 'video_resolution')
        }),
        ('Approval', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'rejection_reason')
        }),
        ('Analytics', {
            'fields': ('view_count', 'average_rating', 'total_ratings')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at')
        }),
    )
    
    actions = ['approve_demos', 'reject_demos']
    
    @admin.action(description="Approve selected demos")
    def approve_demos(self, request, queryset):
        for demo in queryset:
            demo.status = 'APPROVED'
            demo.reviewed_by = request.user
            demo.reviewed_at = timezone.now()
            demo.rejection_reason = None
            demo.save()
        self.message_user(request, f"{queryset.count()} demos approved successfully")
    
    @admin.action(description="Reject selected demos")
    def reject_demos(self, request, queryset):
        for demo in queryset:
            demo.status = 'REJECTED'
            demo.reviewed_by = request.user
            demo.reviewed_at = timezone.now()
            # Admin should add rejection reason manually
            demo.save()
        self.message_user(request, f"{queryset.count()} demos rejected")


@admin.register(DemoRating)
class DemoRatingAdmin(admin.ModelAdmin):
    list_display = ('demo', 'student', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('demo__title', 'student__email', 'review')


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('course', 'order', 'title', 'estimated_hours', 'is_mandatory')
    list_filter = ('course', 'is_mandatory')
    search_fields = ('title', 'course__title', 'description')
    ordering = ('course', 'order')


@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'module', 'completion_percentage', 'is_completed', 'started_at', 'completed_at')
    list_filter = ('is_completed', 'is_started', 'created_at')
    search_fields = ('enrollment__student__email', 'module__title')


@admin.register(LearningRoadmap)
class LearningRoadmapAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'is_active', 'is_completed', 'target_completion_date')
    list_filter = ('is_active', 'is_completed', 'created_at')
    search_fields = ('student__email', 'title', 'goal')


@admin.register(RoadmapCourse)
class RoadmapCourseAdmin(admin.ModelAdmin):
    list_display = ('roadmap', 'order', 'course', 'is_completed')
    list_filter = ('is_completed',)
    search_fields = ('roadmap__title', 'course__title')
    ordering = ('roadmap', 'order')


from django.contrib import admin
from .models import AIConversation, AIMessage, AIFeedback

# ... existing admin classes

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'subject', 'message_count', 'is_active', 'started_at')
    list_filter = ('is_active', 'started_at', 'course')
    search_fields = ('student__email', 'title', 'subject')
    readonly_fields = ('message_count', 'started_at', 'last_message_at', 'ended_at')


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'content_preview', 'model_used', 'tokens_used', 'created_at')
    list_filter = ('role', 'model_used', 'has_audio', 'created_at')
    search_fields = ('content', 'conversation__student__email')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'message', 'rating', 'is_helpful', 'created_at')
    list_filter = ('rating', 'is_helpful', 'created_at')
    search_fields = ('student__email', 'comment')


from django.contrib import admin
from .models import (
    MockTest, MockTestQuestion, MockTestAttempt, MockTestAnswer,
    SessionSummary, StudentProgressAnalytics, RecommendedCourse
)

# ... existing admin classes

@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'subject', 'difficulty', 'total_questions', 'created_at')
    list_filter = ('difficulty', 'is_published', 'created_at')
    search_fields = ('title', 'student__email', 'subject')


@admin.register(MockTestAttempt)
class MockTestAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'mock_test', 'percentage', 'passed', 'status', 'started_at')
    list_filter = ('status', 'passed', 'started_at')
    search_fields = ('student__email', 'mock_test__title')


@admin.register(SessionSummary)
class SessionSummaryAdmin(admin.ModelAdmin):
    list_display = ('session', 'generated_at', 'is_visible_to_student')
    list_filter = ('generated_at', 'is_visible_to_student')
    search_fields = ('session__title', 'summary_text')


@admin.register(StudentProgressAnalytics)
class StudentProgressAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'completion_rate', 'average_test_score', 'learning_pace', 'computed_at')
    list_filter = ('learning_pace', 'at_risk_of_dropout', 'computed_at')
    search_fields = ('student__email', 'course__title')


@admin.register(RecommendedCourse)
class RecommendedCourseAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'confidence_score', 'rank', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('student__email', 'course__title')


from django.contrib import admin
from .models import (
    SupportFAQ, ChatbotConversation, ChatbotMessage,
    SupportTicket, TicketMessage
)

# ... existing admin classes

@admin.register(SupportFAQ)
class SupportFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'view_count', 'helpful_count', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer', 'keywords')
    list_editable = ('order', 'is_active')


@admin.register(ChatbotConversation)
class ChatbotConversationAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'message_count', 'escalated_to_human', 'resolved', 'started_at')
    list_filter = ('escalated_to_human', 'resolved', 'started_at')
    search_fields = ('session_id', 'user__email')
    readonly_fields = ('session_id', 'started_at', 'last_message_at')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'subject', 'user', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('ticket_number', 'subject', 'email', 'name')
    readonly_fields = ('ticket_number', 'created_at')
    
    actions = ['mark_resolved', 'mark_in_progress']
    
    @admin.action(description="Mark as Resolved")
    def mark_resolved(self, request, queryset):
        queryset.update(status='RESOLVED', resolved_at=timezone.now())
    
    @admin.action(description="Mark as In Progress")
    def mark_in_progress(self, request, queryset):
        queryset.update(status='IN_PROGRESS')
