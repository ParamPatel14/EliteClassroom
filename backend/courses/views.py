from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from accounts.models import User, TeacherProfile
from accounts.serializers import UserProfileSerializer
from accounts.permissions import IsStudent, IsTeacher
from .models import Course, Session, Resource, Enrollment, TeacherRating
from .serializers import (
    CourseSerializer, SessionSerializer, SessionCreateSerializer,
    ResourceSerializer, EnrollmentSerializer, TeacherRatingSerializer
)
from django.db.models import F
from .utils_geo import haversine_km



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
    
    def list(self, request, *args, **kwargs):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius_km = float(request.query_params.get('radius_km', '0') or '0')
        queryset = self.get_queryset()

        results = []
        if lat and lon and radius_km > 0:
            lat = float(lat); lon = float(lon)
            for t in queryset:
                if t.latitude and t.longitude:
                    dist = haversine_km(lat, lon, float(t.latitude), float(t.longitude))
                    if dist <= radius_km and getattr(t.teacher_profile, 'available_for_offline', False):
                        results.append((dist, t))
            results.sort(key=lambda x: x[0])
            queryset = [t for _, t in results]

        page = self.paginate_queryset(queryset)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(queryset, many=True)
        return Response(ser.data)


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


from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone as dj_tz
from django.db.models import Sum
import zoneinfo
from accounts.permissions import IsTeacher
from accounts.models import User
from .models import TeacherCredential, TeacherAvailability, TeacherAvailabilityException, Session
from .serializers import (
    TeacherCredentialSerializer, TeacherAvailabilitySerializer,
    TeacherAvailabilityExceptionSerializer, TeacherProfileBuilderSerializer
)

class TeacherSelfGuard(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.teacher_id == request.user.id

class TeacherCredentialListCreateView(generics.ListCreateAPIView):
    serializer_class = TeacherCredentialSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return TeacherCredential.objects.filter(teacher=self.request.user).order_by('-submitted_at')

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

class TeacherCredentialDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = TeacherCredentialSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher, TeacherSelfGuard]

    def get_queryset(self):
        return TeacherCredential.objects.filter(teacher=self.request.user)

class TeacherProfileBuilderView(generics.UpdateAPIView):
    """Update teacher basic info and teacher_profile qualifications."""
    serializer_class = TeacherProfileBuilderSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_object(self):
        return self.request.user

class TeacherAvailabilityListCreateView(generics.ListCreateAPIView):
    serializer_class = TeacherAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return TeacherAvailability.objects.filter(teacher=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

class TeacherAvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeacherAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return TeacherAvailability.objects.filter(teacher=self.request.user)

class TeacherAvailabilityExceptionListCreateView(generics.ListCreateAPIView):
    serializer_class = TeacherAvailabilityExceptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return TeacherAvailabilityException.objects.filter(teacher=self.request.user)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

class TeacherAvailabilityExceptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeacherAvailabilityExceptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return TeacherAvailabilityException.objects.filter(teacher=self.request.user)

class TeacherDashboardView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get(self, request):
        teacher = request.user

        total_students = Session.objects.filter(teacher=teacher).values('student').distinct().count()
        upcoming_sessions = Session.objects.filter(
            teacher=teacher, status__in=['PENDING', 'CONFIRMED']
        ).order_by('scheduled_date', 'start_time')[:5]

        total_earnings = Session.objects.filter(
            teacher=teacher, status='COMPLETED', is_paid=True
        ).aggregate(total=Sum('price'))['total'] or 0

        pending_credentials = TeacherCredential.objects.filter(teacher=teacher, verified=False).count()

        return Response({
            'teacher': teacher.email,
            'stats': {
                'total_students': total_students,
                'upcoming_count': upcoming_sessions.count(),
                'total_earnings': float(total_earnings),
                'pending_verifications': pending_credentials,
            },
            'upcoming_sessions': [{
                'id': s.id, 'title': s.title, 'date': s.scheduled_date,
                'start_time': s.start_time, 'end_time': s.end_time, 'student_email': s.student.email
            } for s in upcoming_sessions]
        })

class TeacherFreeSlotsView(generics.GenericAPIView):
    """Compute teacher free slots from recurring availability minus sessions and exceptions in a requested date range."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, teacher_id):
        from datetime import datetime, timedelta
        try:
            teacher = User.objects.get(id=teacher_id, role='TEACHER', is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)

        start = request.query_params.get('start')  # ISO date e.g. 2025-10-28
        end = request.query_params.get('end')
        tz_name = request.query_params.get('tz', teacher.teacher_profile and getattr(teacher.teacher_profile, 'timezone', 'UTC') or 'UTC')

        if not start or not end:
            return Response({'error': 'start and end query params are required (YYYY-MM-DD)'}, status=400)

        tz = zoneinfo.ZoneInfo(tz_name)  # teacher/user timezone [IANA]
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()

        # Pull recurring availability in teacher timezone terms
        rec_avails = list(TeacherAvailability.objects.filter(teacher=teacher, is_active=True))
        exceptions = list(TeacherAvailabilityException.objects.filter(teacher=teacher, date__range=(start_date, end_date)))

        # Existing sessions in date range
        sessions = list(Session.objects.filter(teacher=teacher, scheduled_date__range=(start_date, end_date)))

        # Build a map date -> list of free intervals (start_time, end_time) in local tz
        from collections import defaultdict
        free = defaultdict(list)

        # Seed with recurring windows
        d = start_date
        while d <= end_date:
            dow = d.weekday()
            for av in rec_avails:
                if av.day_of_week == dow and av.is_active:
                    free[d].append([av.start_time, av.end_time])
            d += timedelta(days=1)

        # Subtract exceptions (block)
        for ex in exceptions:
            if ex.is_blocked and ex.date in free:
                blocked = []
                for (s, e) in free[ex.date]:
                    # remove overlap segment
                    if ex.end_time <= s or ex.start_time >= e:
                        blocked.append([s, e])
                    else:
                        if ex.start_time > s:
                            blocked.append([s, ex.start_time])
                        if ex.end_time < e:
                            blocked.append([ex.end_time, e])
                free[ex.date] = blocked

        # Subtract existing sessions
        for sess in sessions:
            date_key = sess.scheduled_date
            if date_key in free:
                after = []
                for (s, e) in free[date_key]:
                    if sess.end_time <= s or sess.start_time >= e:
                        after.append([s, e])
                    else:
                        if sess.start_time > s:
                            after.append([s, sess.start_time])
                        if sess.end_time < e:
                            after.append([sess.end_time, e])
                free[date_key] = after

        # Return in ISO with times as strings
        resp = []
        for date_key in sorted(free.keys()):
            slots = [{'start': str(s), 'end': str(e)} for (s, e) in free[date_key] if s < e]
            if slots:
                resp.append({'date': str(date_key), 'slots': slots})

        return Response({'timezone': tz_name, 'free': resp})
