from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from accounts.models import User, TeacherProfile
from accounts.permissions import IsStudent, IsTeacher
from .models import Course, Session, Resource, Enrollment, TeacherRating
from .serializers import (
    CourseSerializer, SessionSerializer, SessionCreateSerializer,
    ResourceSerializer, EnrollmentSerializer, TeacherRatingSerializer
)


class TeacherSearchView(generics.ListAPIView):
    """Search and filter teachers"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'teacher_profile__subjects_taught']
    ordering_fields = ['teacher_profile__average_rating', 'teacher_profile__hourly_rate', 
                       'teacher_profile__years_of_experience']
    
    def get_queryset(self):
        queryset = User.objects.filter(role='TEACHER', is_active=True)
        
        # Filter by subject
        subject = self.request.query_params.get('subject', None)
        if subject:
            queryset = queryset.filter(
                teacher_profile__subjects_taught__icontains=subject
            )
        
        # Filter by minimum rating
        min_rating = self.request.query_params.get('min_rating', None)
        if min_rating:
            queryset = queryset.filter(
                teacher_profile__average_rating__gte=float(min_rating)
            )
        
        # Filter by max hourly rate
        max_rate = self.request.query_params.get('max_rate', None)
        if max_rate:
            queryset = queryset.filter(
                teacher_profile__hourly_rate__lte=float(max_rate)
            )
        
        # Filter by location (city)
        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filter by availability type
        availability = self.request.query_params.get('availability', None)
        if availability == 'online':
            queryset = queryset.filter(teacher_profile__available_for_online=True)
        elif availability == 'offline':
            queryset = queryset.filter(teacher_profile__available_for_offline=True)
        
        return queryset.select_related('teacher_profile')


class StudentDashboardView(APIView):
    """Student dashboard with overview data"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get(self, request):
        student = request.user
        
        # Get enrolled courses
        enrollments = Enrollment.objects.filter(student=student).select_related('course')
        
        # Get upcoming sessions
        upcoming_sessions = Session.objects.filter(
            student=student,
            status__in=['PENDING', 'CONFIRMED']
        ).select_related('teacher', 'course').order_by('scheduled_date', 'start_time')[:5]
        
        # Get completed sessions count
        completed_sessions = Session.objects.filter(
            student=student,
            status='COMPLETED'
        ).count()
        
        # Calculate progress
        total_enrollments = enrollments.count()
        completed_enrollments = enrollments.filter(completed=True).count()
        
        return Response({
            'student': UserProfileSerializer(student).data,
            'enrollments': EnrollmentSerializer(enrollments, many=True).data,
            'upcoming_sessions': SessionSerializer(upcoming_sessions, many=True).data,
            'stats': {
                'total_courses': total_enrollments,
                'completed_courses': completed_enrollments,
                'total_sessions': completed_sessions,
            }
        })


class SessionListCreateView(generics.ListCreateAPIView):
    """List and create sessions"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SessionCreateSerializer
        return SessionSerializer
    
    def get_queryset(self):
        return Session.objects.filter(student=self.request.user).select_related(
            'teacher', 'course'
        )
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)


class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or cancel session"""
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        return Session.objects.filter(student=self.request.user)


class ResourceListView(generics.ListAPIView):
    """List free resources, filtered by course enrollment"""
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'description', 'tags']
    filterset_fields = ['resource_type', 'category', 'course']
    
    def get_queryset(self):
        student = self.request.user
        
        # Get enrolled course IDs
        enrolled_course_ids = Enrollment.objects.filter(
            student=student
        ).values_list('course_id', flat=True)
        
        # Return free resources or resources from enrolled courses
        queryset = Resource.objects.filter(
            Q(is_free=True) | 
            Q(course_id__in=enrolled_course_ids, requires_enrollment=True)
        )
        
        return queryset.order_by('-created_at')


class EnrollCourseView(APIView):
    """Enroll student in a course"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id, is_active=True)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already enrolled
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'error': 'Already enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create enrollment
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course
        )
        
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED
        )
