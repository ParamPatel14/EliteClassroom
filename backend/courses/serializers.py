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
