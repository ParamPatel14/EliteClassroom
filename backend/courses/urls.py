from django.urls import path
from .views import (
    TeacherSearchView, StudentDashboardView, SessionListCreateView,
    SessionDetailView, ResourceListView, EnrollCourseView
)

urlpatterns = [
    # Teacher search
    path('teachers/search/', TeacherSearchView.as_view(), name='teacher-search'),
    
    # Student dashboard
    path('student/dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    
    # Sessions/Bookings
    path('sessions/', SessionListCreateView.as_view(), name='session-list-create'),
    path('sessions/<int:pk>/', SessionDetailView.as_view(), name='session-detail'),
    
    # Resources
    path('resources/', ResourceListView.as_view(), name='resource-list'),
    
    # Enrollment
    path('courses/<int:course_id>/enroll/', EnrollCourseView.as_view(), name='enroll-course'),
]

from django.urls import path
from .views import (
  TeacherCredentialListCreateView, TeacherCredentialDetailView,
  TeacherProfileBuilderView, TeacherAvailabilityListCreateView, TeacherAvailabilityDetailView,
  TeacherAvailabilityExceptionListCreateView, TeacherAvailabilityExceptionDetailView,
  TeacherDashboardView, TeacherFreeSlotsView
)

urlpatterns += [
    # Teacher profile & credentials
    path('teacher/profile/', TeacherProfileBuilderView.as_view(), name='teacher-profile-builder'),
    path('teacher/credentials/', TeacherCredentialListCreateView.as_view(), name='teacher-credentials'),
    path('teacher/credentials/<int:pk>/', TeacherCredentialDetailView.as_view(), name='teacher-credential-detail'),

    # Teacher availability
    path('teacher/availability/', TeacherAvailabilityListCreateView.as_view(), name='teacher-availability'),
    path('teacher/availability/<int:pk>/', TeacherAvailabilityDetailView.as_view(), name='teacher-availability-detail'),
    path('teacher/availability/exceptions/', TeacherAvailabilityExceptionListCreateView.as_view(), name='teacher-availability-exceptions'),
    path('teacher/availability/exceptions/<int:pk>/', TeacherAvailabilityExceptionDetailView.as_view(), name='teacher-availability-exception-detail'),

    # Teacher dashboard and free slots
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher-dashboard'),
    path('teachers/<int:teacher_id>/free-slots/', TeacherFreeSlotsView.as_view(), name='teacher-free-slots'),
]
