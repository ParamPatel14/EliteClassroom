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
