from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
import uuid

from .models import (
    SupportFAQ, ChatbotConversation, ChatbotMessage,
    SupportTicket, TicketMessage
)
from .serializers import (
    SupportFAQSerializer, ChatbotConversationSerializer,
    ChatbotMessageSerializer, SupportTicketSerializer,
    TicketMessageSerializer
)
from .chatbot_service import ChatbotEngine, KnowledgeBase


class ChatbotInitView(APIView):
    """Initialize or retrieve chatbot conversation"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        
        # If no session_id, create new conversation
        if not session_id:
            session_id = str(uuid.uuid4())
            
            conversation = ChatbotConversation.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                page_url=request.data.get('page_url', ''),
                referrer=request.META.get('HTTP_REFERER', '')
            )
            
            # Create welcome message
            ChatbotMessage.objects.create(
                conversation=conversation,
                role='bot',
                content="Hi! I'm here to help. What can I assist you with today?"
            )
        else:
            # Retrieve existing conversation
            try:
                conversation = ChatbotConversation.objects.get(session_id=session_id)
            except ChatbotConversation.DoesNotExist:
                return Response({'error': 'Invalid session'}, status=404)
        
        # Return conversation with recent messages
        messages = conversation.messages.order_by('-created_at')[:20]
        
        return Response({
            'session_id': conversation.session_id,
            'messages': ChatbotMessageSerializer(reversed(messages), many=True).data,
            'user_context': {
                'is_authenticated': request.user.is_authenticated,
                'name': request.user.first_name if request.user.is_authenticated else None,
                'role': request.user.role if request.user.is_authenticated else None
            }
        })


class ChatbotMessageView(APIView):
    """Send message to chatbot and get response"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        user_message = request.data.get('message')
        
        if not session_id or not user_message:
            return Response({'error': 'session_id and message required'}, status=400)
        
        try:
            conversation = ChatbotConversation.objects.get(session_id=session_id)
        except ChatbotConversation.DoesNotExist:
            return Response({'error': 'Invalid session'}, status=404)
        
        # Save user message
        user_msg = ChatbotMessage.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )
        
        # Get conversation history
        history = []
        for msg in conversation.messages.order_by('created_at'):
            if msg.role in ['user', 'bot']:
                history.append({
                    'role': 'assistant' if msg.role == 'bot' else msg.role,
                    'content': msg.content
                })
        
        # Build user context
        user_context = {}
        if request.user.is_authenticated:
            user_context = {
                'is_authenticated': True,
                'name': request.user.first_name,
                'email': request.user.email,
                'role': request.user.role
            }
        
        # Generate response
        try:
            bot_response = ChatbotEngine.generate_response(
                user_message=user_message,
                conversation_history=history,
                user_context=user_context
            )
            
            # Save bot message
            bot_msg = ChatbotMessage.objects.create(
                conversation=conversation,
                role='bot',
                content=bot_response['response'],
                intent_detected=bot_response.get('intent'),
                confidence_score=bot_response.get('confidence'),
                faq_matched_id=bot_response.get('faq_matched'),
                model_used=bot_response.get('model_used'),
                tokens_used=bot_response.get('tokens_used', 0)
            )
            
            # Update conversation
            conversation.message_count = conversation.messages.count()
            conversation.last_message_at = timezone.now()
            conversation.save()
            
            # Increment FAQ view count if matched
            if bot_response.get('faq_matched'):
                SupportFAQ.objects.filter(id=bot_response['faq_matched']).update(
                    view_count=models.F('view_count') + 1
                )
            
            return Response({
                'message': ChatbotMessageSerializer(bot_msg).data,
                'suggested_actions': bot_response.get('suggested_actions', []),
                'escalation_suggested': bot_response.get('escalation_suggested', False)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Bot response failed: {str(e)}'},
                status=500
            )


class FAQListView(generics.ListAPIView):
    """Browse all FAQs by category"""
    serializer_class = SupportFAQSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = SupportFAQ.objects.filter(is_active=True)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(question__icontains=search) |
                models.Q(answer__icontains=search)
            )
        
        return queryset.order_by('category', 'order')


class FAQDetailView(generics.RetrieveAPIView):
    """Get single FAQ and mark as helpful"""
    serializer_class = SupportFAQSerializer
    permission_classes = [permissions.AllowAny]
    queryset = SupportFAQ.objects.filter(is_active=True)


class FAQFeedbackView(APIView):
    """Mark FAQ as helpful or not helpful"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, faq_id):
        is_helpful = request.data.get('helpful', True)
        
        try:
            faq = SupportFAQ.objects.get(id=faq_id, is_active=True)
        except SupportFAQ.DoesNotExist:
            return Response({'error': 'FAQ not found'}, status=404)
        
        if is_helpful:
            faq.helpful_count += 1
        else:
            faq.not_helpful_count += 1
        
        faq.save()
        
        return Response({'success': True})


class CreateSupportTicketView(APIView):
    """Escalate conversation to human support"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        subject = request.data.get('subject')
        description = request.data.get('description')
        category = request.data.get('category', 'GENERAL')
        email = request.data.get('email')
        name = request.data.get('name')
        
        if not all([subject, description, email, name]):
            return Response(
                {'error': 'subject, description, email, and name required'},
                status=400
            )
        
        # Get conversation if provided
        conversation = None
        if session_id:
            try:
                conversation = ChatbotConversation.objects.get(session_id=session_id)
                conversation.escalated_to_human = True
                conversation.save()
            except ChatbotConversation.DoesNotExist:
                pass
        
        # Create ticket
        ticket = SupportTicket.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=email,
            name=name,
            subject=subject,
            description=description,
            category=category,
            conversation=conversation,
            page_url=request.data.get('page_url', '')
        )
        
        # Add initial message
        if description:
            TicketMessage.objects.create(
                ticket=ticket,
                sender=request.user if request.user.is_authenticated else None,
                message=description,
                is_staff_reply=False
            )
        
        return Response(
            SupportTicketSerializer(ticket).data,
            status=status.HTTP_201_CREATED
        )


class UserTicketsView(generics.ListAPIView):
    """List user's support tickets"""
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SupportTicket.objects.filter(user=request.user).order_by('-created_at')


class TicketDetailView(generics.RetrieveAPIView):
    """Get ticket with message thread"""
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)


class ConversationFeedbackView(APIView):
    """Submit feedback on chatbot conversation"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, session_id):
        try:
            conversation = ChatbotConversation.objects.get(session_id=session_id)
        except ChatbotConversation.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        
        conversation.user_satisfaction = request.data.get('rating')
        conversation.feedback_comment = request.data.get('comment', '')
        conversation.resolved = request.data.get('resolved', False)
        conversation.ended_at = timezone.now()
        conversation.save()
        
        return Response({'success': True})
