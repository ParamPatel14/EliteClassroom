from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView, EmailVerificationView, ResendVerificationEmailView,
    UserLoginView, UserLogoutView, UserProfileView, 
    StudentProfileUpdateView, TeacherProfileUpdateView, UserListView
)

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-email/<str:uidb64>/<str:token>/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile endpoints
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/student/', StudentProfileUpdateView.as_view(), name='student-profile'),
    path('profile/teacher/', TeacherProfileUpdateView.as_view(), name='teacher-profile'),
    
    # Admin endpoints
    path('users/', UserListView.as_view(), name='user-list'),
]
