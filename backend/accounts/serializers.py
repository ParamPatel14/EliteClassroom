from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, StudentProfile, TeacherProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 
                  'role', 'phone_number', 'date_of_birth']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if attrs['role'] not in ['STUDENT', 'TEACHER']:
            raise serializers.ValidationError({"role": "Role must be either STUDENT or TEACHER."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create corresponding profile
        if user.role == 'STUDENT':
            StudentProfile.objects.create(user=user)
        elif user.role == 'TEACHER':
            TeacherProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "email" and "password".')


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for student profile"""
    
    class Meta:
        model = StudentProfile
        fields = ['grade_level', 'subjects_interested', 'learning_goals', 'preferred_learning_style']


class TeacherProfileSerializer(serializers.ModelSerializer):
    """Serializer for teacher profile"""
    
    class Meta:
        model = TeacherProfile
        fields = ['highest_degree', 'university', 'specialization', 'years_of_experience',
                  'subjects_taught', 'teaching_languages', 'hourly_rate', 'is_verified',
                  'available_for_offline', 'available_for_online', 'average_rating', 
                  'total_reviews', 'total_sessions']
        read_only_fields = ['is_verified', 'average_rating', 'total_reviews', 'total_sessions']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with role-specific data"""
    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role', 
                  'phone_number', 'profile_picture', 'date_of_birth', 'bio',
                  'address_line1', 'address_line2', 'city', 'state', 'country', 
                  'postal_code', 'latitude', 'longitude', 'is_email_verified',
                  'is_phone_verified', 'created_at', 'student_profile', 'teacher_profile']
        read_only_fields = ['id', 'email', 'role', 'created_at', 'is_email_verified', 
                            'is_phone_verified']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile_picture', 
                  'date_of_birth', 'bio', 'address_line1', 'address_line2', 
                  'city', 'state', 'country', 'postal_code', 'latitude', 'longitude']
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
