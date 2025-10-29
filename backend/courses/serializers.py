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
