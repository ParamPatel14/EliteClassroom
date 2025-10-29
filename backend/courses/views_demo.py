from rest_framework import generics, permissions, status, filters
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, F
from django.utils import timezone
from accounts.permissions import IsStudent, IsTeacher
from .models import DemoLecture, DemoRating, CourseModule, ModuleProgress, LearningRoadmap, Enrollment
from .serializers import (
    DemoLectureSerializer, DemoLectureUploadSerializer, DemoRatingSerializer,
    CourseModuleSerializer, ModuleProgressSerializer, LearningRoadmapSerializer,
    LearningRoadmapCreateSerializer
)


class DemoLectureListView(generics.ListAPIView):
    """Public list of approved demo lectures with search/filter"""
    serializer_class = DemoLectureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'subject', 'teacher__first_name', 'teacher__last_name']
    ordering_fields = ['average_rating', 'view_count', 'uploaded_at']
    ordering = ['-average_rating', '-view_count']
    
    def get_queryset(self):
        queryset = DemoLecture.objects.filter(status='APPROVED').select_related('teacher')
        
        # Filter by subject
        subject = self.request.query_params.get('subject')
        if subject:
            queryset = queryset.filter(subject__icontains=subject)
        
        # Filter by teacher
        teacher_id = self.request.query_params.get('teacher_id')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Min rating filter
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=float(min_rating))
        
        return queryset


class DemoLectureDetailView(generics.RetrieveAPIView):
    """Get demo detail and increment view count"""
    serializer_class = DemoLectureSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DemoLecture.objects.filter(status='APPROVED')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        DemoLecture.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class TeacherDemoUploadView(generics.CreateAPIView):
    """Teacher uploads demo lecture"""
    serializer_class = DemoLectureUploadSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def perform_create(self, serializer):
        demo = serializer.save(teacher=self.request.user, status='PENDING')
        # TODO: Trigger async transcoding task here (Celery + FFmpeg)
        # For now, just save original video
        demo.file_size_mb = demo.original_video.size / (1024 * 1024)
        demo.save()


class TeacherDemoListView(generics.ListAPIView):
    """Teacher's own demos"""
    serializer_class = DemoLectureSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def get_queryset(self):
        return DemoLecture.objects.filter(teacher=self.request.user)


class DemoRatingCreateView(generics.CreateAPIView):
    """Student rates a demo"""
    serializer_class = DemoRatingSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def perform_create(self, serializer):
        demo = serializer.validated_data['demo']
        
        # Check if already rated
        if DemoRating.objects.filter(demo=demo, student=self.request.user).exists():
            raise serializers.ValidationError("You have already rated this demo")
        
        rating = serializer.save(student=self.request.user)
        
        # Update demo average rating
        avg = DemoRating.objects.filter(demo=demo).aggregate(Avg('rating'))['rating__avg']
        count = DemoRating.objects.filter(demo=demo).count()
        demo.average_rating = round(avg, 2)
        demo.total_ratings = count
        demo.save()


class DemoRatingListView(generics.ListAPIView):
    """List ratings for a demo"""
    serializer_class = DemoRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        demo_id = self.kwargs.get('demo_id')
        return DemoRating.objects.filter(demo_id=demo_id).select_related('student')


class CourseModuleListView(generics.ListAPIView):
    """List modules for a course"""
    serializer_class = CourseModuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return CourseModule.objects.filter(course_id=course_id).order_by('order')


class ModuleProgressListView(generics.ListAPIView):
    """Student's progress across course modules"""
    serializer_class = ModuleProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        enrollment_id = self.kwargs.get('enrollment_id')
        return ModuleProgress.objects.filter(
            enrollment_id=enrollment_id,
            enrollment__student=self.request.user
        ).select_related('module')


class ModuleProgressUpdateView(generics.UpdateAPIView):
    """Update student progress on a module"""
    serializer_class = ModuleProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        return ModuleProgress.objects.filter(enrollment__student=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        
        # Auto-mark as started if not already
        if not instance.is_started:
            instance.is_started = True
            instance.started_at = timezone.now()
        
        # Auto-mark as completed if 100%
        if instance.completion_percentage >= 100 and not instance.is_completed:
            instance.is_completed = True
            instance.completed_at = timezone.now()
        
        instance.save()
        
        # Update overall enrollment progress
        enrollment = instance.enrollment
        total_modules = enrollment.course.modules.count()
        if total_modules > 0:
            completed = ModuleProgress.objects.filter(
                enrollment=enrollment,
                is_completed=True
            ).count()
            enrollment.progress = round((completed / total_modules) * 100, 2)
            enrollment.save()


class LearningRoadmapListCreateView(generics.ListCreateAPIView):
    """List and create student roadmaps"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LearningRoadmapCreateSerializer
        return LearningRoadmapSerializer
    
    def get_queryset(self):
        return LearningRoadmap.objects.filter(student=self.request.user).prefetch_related('courses')
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)


class LearningRoadmapDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a roadmap"""
    serializer_class = LearningRoadmapSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        return LearningRoadmap.objects.filter(student=self.request.user)
