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

from django.urls import path
from .views_rtc import SessionJoinTokenView, SessionRecordingWebhookView

urlpatterns += [
    path('rtc/session/<int:session_id>/join-token/', SessionJoinTokenView.as_view(), name='rtc-join-token'),
    path('rtc/recording/webhook/', SessionRecordingWebhookView.as_view(), name='rtc-recording-webhook'),
]

from django.urls import path
from .views_demo import (
    DemoLectureListView, DemoLectureDetailView, TeacherDemoUploadView,
    TeacherDemoListView, DemoRatingCreateView, DemoRatingListView,
    CourseModuleListView, ModuleProgressListView, ModuleProgressUpdateView,
    LearningRoadmapListCreateView, LearningRoadmapDetailView
)

urlpatterns += [
    # Demo lectures
    path('demos/', DemoLectureListView.as_view(), name='demo-list'),
    path('demos/<int:pk>/', DemoLectureDetailView.as_view(), name='demo-detail'),
    path('teacher/demos/', TeacherDemoListView.as_view(), name='teacher-demo-list'),
    path('teacher/demos/upload/', TeacherDemoUploadView.as_view(), name='teacher-demo-upload'),
    
    # Demo ratings
    path('demos/<int:demo_id>/ratings/', DemoRatingListView.as_view(), name='demo-rating-list'),
    path('demos/rate/', DemoRatingCreateView.as_view(), name='demo-rate'),
    
    # Course modules and progress
    path('courses/<int:course_id>/modules/', CourseModuleListView.as_view(), name='course-modules'),
    path('enrollments/<int:enrollment_id>/progress/', ModuleProgressListView.as_view(), name='module-progress'),
    path('progress/<int:pk>/update/', ModuleProgressUpdateView.as_view(), name='module-progress-update'),
    
    # Learning roadmaps
    path('student/roadmaps/', LearningRoadmapListCreateView.as_view(), name='roadmap-list-create'),
    path('student/roadmaps/<int:pk>/', LearningRoadmapDetailView.as_view(), name='roadmap-detail'),
]


from django.urls import path
from .views_ai import (
    AIConversationListCreateView, AIConversationDetailView,
    AIChatView, AIVoiceChatView, AIMessageListView, AIFeedbackView
)

urlpatterns += [
    # AI Tutor endpoints
    path('ai/conversations/', AIConversationListCreateView.as_view(), name='ai-conversation-list'),
    path('ai/conversations/<int:pk>/', AIConversationDetailView.as_view(), name='ai-conversation-detail'),
    path('ai/conversations/<int:conversation_id>/chat/', AIChatView.as_view(), name='ai-chat'),
    path('ai/conversations/<int:conversation_id>/voice/', AIVoiceChatView.as_view(), name='ai-voice-chat'),
    path('ai/conversations/<int:conversation_id>/messages/', AIMessageListView.as_view(), name='ai-messages'),
    path('ai/feedback/', AIFeedbackView.as_view(), name='ai-feedback'),
]


from django.urls import path
from .views_assessment import (
    GenerateMockTestView, MockTestListView, StartMockTestView,
    SubmitMockTestView, MockTestAttemptListView, GenerateSessionSummaryView,
    StudentAnalyticsView, CourseRecommendationsView
)

urlpatterns += [
    # Mock Tests
    path('sessions/<int:session_id>/generate-test/', GenerateMockTestView.as_view(), name='generate-test'),
    path('tests/', MockTestListView.as_view(), name='test-list'),
    path('tests/<int:test_id>/start/', StartMockTestView.as_view(), name='start-test'),
    path('tests/attempts/<int:attempt_id>/submit/', SubmitMockTestView.as_view(), name='submit-test'),
    path('tests/attempts/', MockTestAttemptListView.as_view(), name='attempt-list'),
    
    # Session Summaries
    path('sessions/<int:session_id>/generate-summary/', GenerateSessionSummaryView.as_view(), name='generate-summary'),
    
    # Analytics & Recommendations
    path('student/analytics/', StudentAnalyticsView.as_view(), name='student-analytics'),
    path('student/recommendations/', CourseRecommendationsView.as_view(), name='course-recommendations'),
]


from django.urls import path
from .views_chatbot import (
    ChatbotInitView, ChatbotMessageView, FAQListView, FAQDetailView,
    FAQFeedbackView, CreateSupportTicketView, UserTicketsView,
    TicketDetailView, ConversationFeedbackView
)

urlpatterns += [
    # Chatbot
    path('chatbot/init/', ChatbotInitView.as_view(), name='chatbot-init'),
    path('chatbot/message/', ChatbotMessageView.as_view(), name='chatbot-message'),
    path('chatbot/<str:session_id>/feedback/', ConversationFeedbackView.as_view(), name='chatbot-feedback'),
    
    # FAQs
    path('faqs/', FAQListView.as_view(), name='faq-list'),
    path('faqs/<int:pk>/', FAQDetailView.as_view(), name='faq-detail'),
    path('faqs/<int:faq_id>/feedback/', FAQFeedbackView.as_view(), name='faq-feedback'),
    
    # Support Tickets
    path('support/tickets/create/', CreateSupportTicketView.as_view(), name='create-ticket'),
    path('support/tickets/', UserTicketsView.as_view(), name='user-tickets'),
    path('support/tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
]

from django.urls import path
from .views_payment import (
    CreatePaymentOrderView, VerifyPaymentView, PaymentWebhookView,
    RequestRefundView, ProcessRefundView, TeacherEarningsView,
    AddBankAccountView, DownloadInvoiceView
)

urlpatterns += [
    # Payments
    path('payments/create-order/', CreatePaymentOrderView.as_view(), name='create-payment-order'),
    path('payments/verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    
    # Refunds
    path('payments/<int:payment_id>/refund/', RequestRefundView.as_view(), name='request-refund'),
    path('refunds/<int:refund_id>/process/', ProcessRefundView.as_view(), name='process-refund'),
    
    # Teacher
    path('teacher/earnings/', TeacherEarningsView.as_view(), name='teacher-earnings'),
    path('teacher/bank-account/', AddBankAccountView.as_view(), name='add-bank-account'),
    
    # Invoices
    path('invoices/<int:invoice_id>/download/', DownloadInvoiceView.as_view(), name='download-invoice'),
]


