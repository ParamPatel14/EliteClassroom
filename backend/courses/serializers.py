from rest_framework import serializers
from .models import Course, Enrollment, Session, Resource, TeacherRating
from accounts.serializers import UserProfileSerializer


class CourseSerializer(serializers.ModelSerializer):
    teacher = UserProfileSerializer(read_only=True)
    enrolled_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = '__all__'
    
    def get_enrolled_count(self, obj):
        return obj.enrollments.count()


class SessionSerializer(serializers.ModelSerializer):
    student = UserProfileSerializer(read_only=True)
    teacher = UserProfileSerializer(read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Session
        fields = '__all__'
        read_only_fields = ['student', 'status', 'created_at', 'updated_at']


class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['teacher', 'course', 'title', 'description', 'session_type',
                  'scheduled_date', 'start_time', 'end_time', 'duration_minutes',
                  'location', 'student_notes']
    
    def create(self, validated_data):
        # Student is set from request.user in view
        return Session.objects.create(**validated_data)


class ResourceSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Resource
        fields = '__all__'


class TeacherRatingSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    
    class Meta:
        model = TeacherRating
        fields = '__all__'
        read_only_fields = ['student', 'created_at', 'updated_at']


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    student = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = '__all__'


from rest_framework import serializers
from .models import TeacherCredential, TeacherAvailability, TeacherAvailabilityException
from accounts.serializers import UserProfileSerializer
from accounts.models import User

class TeacherCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherCredential
        fields = ['id', 'degree', 'institution', 'year', 'certification_name', 'achievement', 'document', 'verified', 'submitted_at', 'verified_at']
        read_only_fields = ['verified', 'submitted_at', 'verified_at']

class TeacherProfileBuilderSerializer(serializers.ModelSerializer):
    """Allows teacher to update extended profile fields."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'city', 'state', 'country']

class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAvailability
        fields = ['id', 'day_of_week', 'start_time', 'end_time', 'timezone', 'is_recurring', 'is_active']

    def validate(self, attrs):
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError("start_time must be before end_time")
        return attrs

class TeacherAvailabilityExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAvailabilityException
        fields = ['id', 'date', 'start_time', 'end_time', 'reason', 'is_blocked']

    def validate(self, attrs):
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError("start_time must be before end_time")
        return attrs


from rest_framework import serializers
from .models import (
    DemoLecture, DemoRating, CourseModule, ModuleProgress,
    LearningRoadmap, RoadmapCourse, Course, Enrollment
)
from accounts.serializers import UserProfileSerializer

# ... existing serializers

class DemoLectureSerializer(serializers.ModelSerializer):
    teacher = UserProfileSerializer(read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    
    class Meta:
        model = DemoLecture
        fields = [
            'id', 'teacher', 'teacher_name', 'course', 'title', 'description',
            'subject', 'duration_minutes', 'transcoded_video', 'thumbnail',
            'status', 'view_count', 'average_rating', 'total_ratings',
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = [
            'teacher', 'status', 'view_count', 'average_rating',
            'total_ratings', 'uploaded_at', 'updated_at'
        ]


class DemoLectureUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoLecture
        fields = [
            'course', 'title', 'description', 'subject',
            'duration_minutes', 'original_video', 'thumbnail'
        ]
    
    def validate_original_video(self, value):
        # Check file size (max 500MB for demo)
        if value.size > 500 * 1024 * 1024:
            raise serializers.ValidationError("Video file too large. Max 500MB")
        # Check extension
        ext = value.name.split('.')[-1].lower()
        if ext not in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
            raise serializers.ValidationError("Invalid video format")
        return value


class DemoRatingSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    
    class Meta:
        model = DemoRating
        fields = ['id', 'demo', 'student', 'student_name', 'rating', 'review', 'created_at']
        read_only_fields = ['student', 'created_at']
    
    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class CourseModuleSerializer(serializers.ModelSerializer):
    prerequisite_titles = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseModule
        fields = [
            'id', 'course', 'title', 'description', 'order',
            'content', 'video_url', 'resources', 'estimated_hours',
            'is_mandatory', 'prerequisite_modules', 'prerequisite_titles'
        ]
    
    def get_prerequisite_titles(self, obj):
        return [m.title for m in obj.prerequisite_modules.all()]


class ModuleProgressSerializer(serializers.ModelSerializer):
    module = CourseModuleSerializer(read_only=True)
    module_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ModuleProgress
        fields = [
            'id', 'enrollment', 'module', 'module_id', 'is_started',
            'is_completed', 'completion_percentage', 'started_at',
            'completed_at', 'time_spent_minutes', 'quiz_score', 'attempts'
        ]
        read_only_fields = ['enrollment', 'created_at', 'updated_at']


class RoadmapCourseSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    
    class Meta:
        model = RoadmapCourse
        fields = ['id', 'order', 'course', 'is_completed']


class LearningRoadmapSerializer(serializers.ModelSerializer):
    courses = RoadmapCourseSerializer(source='roadmapcourse_set', many=True, read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningRoadmap
        fields = [
            'id', 'student', 'title', 'description', 'goal',
            'target_completion_date', 'estimated_hours_per_week',
            'courses', 'progress_percentage', 'is_active',
            'is_completed', 'created_at'
        ]
        read_only_fields = ['student', 'created_at']
    
    def get_progress_percentage(self, obj):
        total = obj.roadmapcourse_set.count()
        if total == 0:
            return 0
        completed = obj.roadmapcourse_set.filter(is_completed=True).count()
        return round((completed / total) * 100, 2)


class LearningRoadmapCreateSerializer(serializers.ModelSerializer):
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    
    class Meta:
        model = LearningRoadmap
        fields = [
            'title', 'description', 'goal', 'target_completion_date',
            'estimated_hours_per_week', 'course_ids'
        ]
    
    def create(self, validated_data):
        course_ids = validated_data.pop('course_ids')
        roadmap = LearningRoadmap.objects.create(**validated_data)
        
        for idx, course_id in enumerate(course_ids):
            RoadmapCourse.objects.create(
                roadmap=roadmap,
                course_id=course_id,
                order=idx
            )
        
        return roadmap


from rest_framework import serializers
from .models import AIConversation, AIMessage, AIFeedback

# ... existing serializers

class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = [
            'id', 'conversation', 'role', 'content', 'has_audio',
            'audio_file', 'audio_duration_seconds', 'model_used',
            'tokens_used', 'response_time_ms', 'created_at'
        ]
        read_only_fields = ['conversation', 'created_at']


class AIConversationSerializer(serializers.ModelSerializer):
    recent_messages = serializers.SerializerMethodField()
    
    class Meta:
        model = AIConversation
        fields = [
            'id', 'student', 'course', 'title', 'subject', 'student_goal',
            'message_count', 'duration_minutes', 'started_at',
            'last_message_at', 'ended_at', 'is_active', 'recent_messages'
        ]
        read_only_fields = ['student', 'message_count', 'started_at', 'last_message_at']
    
    def get_recent_messages(self, obj):
        messages = obj.messages.order_by('-created_at')[:5]
        return AIMessageSerializer(messages, many=True).data


class AIFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback
        fields = ['id', 'message', 'student', 'rating', 'comment', 'is_helpful', 'created_at']
        read_only_fields = ['student', 'created_at']
    
    def validate_message(self, value):
        # Ensure message belongs to requesting student
        request = self.context.get('request')
        if value.conversation.student != request.user:
            raise serializers.ValidationError("Cannot rate messages from other students")
        return value


from rest_framework import serializers
from .models import (
    MockTest, MockTestQuestion, MockTestAttempt, MockTestAnswer,
    SessionSummary, StudentProgressAnalytics, RecommendedCourse
)

# ... existing serializers

class MockTestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MockTestQuestion
        fields = [
            'id', 'order', 'question_type', 'question_text', 'options',
            'points', 'bloom_level', 'explanation'
        ]
        # Hide correct_answer in student view


class MockTestSerializer(serializers.ModelSerializer):
    questions = MockTestQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = MockTest
        fields = [
            'id', 'title', 'description', 'subject', 'difficulty',
            'total_questions', 'duration_minutes', 'passing_score',
            'is_published', 'created_at', 'questions'
        ]


class MockTestAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='question.correct_answer', read_only=True)
    
    class Meta:
        model = MockTestAnswer
        fields = [
            'id', 'question', 'question_text', 'selected_answer',
            'correct_answer', 'is_correct', 'points_earned', 'ai_feedback'
        ]
        read_only_fields = ['is_correct', 'points_earned', 'ai_feedback']


class MockTestAttemptSerializer(serializers.ModelSerializer):
    mock_test = MockTestSerializer(read_only=True)
    answers = MockTestAnswerSerializer(many=True, read_only=True)
    scorecard_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MockTestAttempt
        fields = [
            'id', 'mock_test', 'status', 'total_score', 'max_score',
            'percentage', 'passed', 'started_at', 'submitted_at',
            'time_taken_minutes', 'scorecard_pdf', 'scorecard_url', 'answers'
        ]
        read_only_fields = [
            'total_score', 'max_score', 'percentage', 'passed',
            'started_at', 'scorecard_pdf'
        ]
    
    def get_scorecard_url(self, obj):
        if obj.scorecard_pdf:
            return obj.scorecard_pdf.url
        return None


class SessionSummarySerializer(serializers.ModelSerializer):
    session_title = serializers.CharField(source='session.title', read_only=True)
    
    class Meta:
        model = SessionSummary
        fields = [
            'id', 'session', 'session_title', 'summary_text', 'key_topics',
            'action_items', 'generated_at', 'is_visible_to_student'
        ]


class StudentProgressAnalyticsSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = StudentProgressAnalytics
        fields = [
            'id', 'course', 'course_title', 'total_sessions', 'total_test_attempts',
            'average_test_score', 'modules_completed', 'modules_in_progress',
            'completion_rate', 'total_learning_hours', 'avg_session_duration_minutes',
            'last_activity_date', 'strengths', 'weaknesses', 'recommended_topics',
            'learning_pace', 'predicted_completion_date', 'at_risk_of_dropout',
            'dropout_risk_score', 'computed_at'
        ]


class RecommendedCourseSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    
    class Meta:
        model = RecommendedCourse
        fields = ['id', 'course', 'confidence_score', 'reason', 'rank', 'created_at']


from rest_framework import serializers
from .models import (
    SupportFAQ, ChatbotConversation, ChatbotMessage,
    SupportTicket, TicketMessage
)

# ... existing serializers

class SupportFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportFAQ
        fields = [
            'id', 'category', 'question', 'answer', 'keywords',
            'view_count', 'helpful_count', 'not_helpful_count'
        ]


class ChatbotMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotMessage
        fields = [
            'id', 'role', 'content', 'intent_detected',
            'confidence_score', 'created_at'
        ]


class ChatbotConversationSerializer(serializers.ModelSerializer):
    messages = ChatbotMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatbotConversation
        fields = [
            'id', 'session_id', 'message_count', 'escalated_to_human',
            'resolved', 'started_at', 'messages'
        ]


class TicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    
    class Meta:
        model = TicketMessage
        fields = ['id', 'sender', 'sender_name', 'is_staff_reply', 'message', 'created_at']


class SupportTicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_number', 'subject', 'description', 'category',
            'priority', 'status', 'created_at', 'updated_at', 'messages'
        ]


from rest_framework import serializers
from .models import Payment, Payout, Refund, Invoice, TeacherBankAccount

# ... existing serializers

class PaymentSerializer(serializers.ModelSerializer):
    session_title = serializers.CharField(source='session.title', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'student', 'session', 'session_title', 'course', 'course_title',
            'payment_type', 'amount', 'platform_fee', 'teacher_amount', 'currency',
            'razorpay_order_id', 'razorpay_payment_id', 'status', 'is_held_in_escrow',
            'escrow_release_date', 'released_from_escrow', 'payment_method',
            'created_at', 'captured_at'
        ]
        read_only_fields = ['student', 'platform_fee', 'teacher_amount', 'created_at']


class PayoutSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    
    class Meta:
        model = Payout
        fields = [
            'id', 'teacher', 'teacher_name', 'payment', 'amount', 'currency',
            'status', 'bank_name', 'created_at', 'processed_at', 'completed_at'
        ]


class RefundSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    payment_amount = serializers.DecimalField(source='payment.amount', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'payment_amount', 'student', 'student_name',
            'refund_amount', 'reason', 'description', 'status', 'admin_notes',
            'requested_at', 'reviewed_at', 'completed_at'
        ]
        read_only_fields = ['student', 'requested_at']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_date', 'student_name',
            'student_email', 'subtotal', 'tax_amount', 'total_amount',
            'pdf_file', 'created_at'
        ]


class TeacherBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherBankAccount
        fields = [
            'id', 'account_holder_name', 'account_number', 'ifsc_code',
            'bank_name', 'branch_name', 'is_verified', 'verified_at'
        ]
        extra_kwargs = {
            'account_number': {'write_only': True}  # Don't expose in responses
        }
