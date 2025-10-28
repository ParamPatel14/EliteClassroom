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
