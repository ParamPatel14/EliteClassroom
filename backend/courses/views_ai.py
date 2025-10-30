from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction
import base64
import io

from accounts.permissions import IsStudent
from .models import AIConversation, AIMessage, AIFeedback, Course
from .serializers import (
    AIConversationSerializer, AIMessageSerializer, AIFeedbackSerializer
)
from .ai_service import LLMService, SpeechService, ConversationManager


class AIConversationListCreateView(generics.ListCreateAPIView):
    """List and create AI tutoring sessions"""
    serializer_class = AIConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        return AIConversation.objects.filter(
            student=self.request.user,
            is_active=True
        ).prefetch_related('messages')
    
    def perform_create(self, serializer):
        course = serializer.validated_data.get('course')
        goal = serializer.validated_data.get('student_goal', '')
        
        # Generate system prompt
        system_prompt = LLMService.create_system_prompt(
            student_name=self.request.user.first_name,
            subject=course.title if course else "General",
            goal=goal
        )
        
        conversation = serializer.save(
            student=self.request.user,
            system_prompt=system_prompt
        )
        
        # Create initial system message
        AIMessage.objects.create(
            conversation=conversation,
            role='system',
            content=system_prompt
        )


class AIConversationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or end AI conversation"""
    serializer_class = AIConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        return AIConversation.objects.filter(student=self.request.user)
    
    def perform_destroy(self, instance):
        """End conversation instead of deleting"""
        instance.is_active = False
        instance.ended_at = timezone.now()
        instance.save()


class AIChatView(APIView):
    """Send message to AI tutor and get response"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request, conversation_id):
        user_message = request.data.get('message')
        
        if not user_message:
            return Response(
                {"error": "Message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation = AIConversation.objects.get(
                id=conversation_id,
                student=request.user,
                is_active=True
            )
        except AIConversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Save user message
        user_msg = AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )
        
        # Get context
        context = ConversationManager.get_context_messages(conversation_id)
        
        # Add current user message
        context.append({"role": "user", "content": user_message})
        
        # Generate AI response
        try:
            response_data = LLMService.generate_response(
                messages=context,
                temperature=0.7,
                max_tokens=500
            )
            
            # Save assistant message
            assistant_msg = AIMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=response_data['content'],
                model_used=response_data['model'],
                tokens_used=response_data['tokens'],
                response_time_ms=response_data['time_ms']
            )
            
            # Update conversation stats
            conversation.message_count += 2  # user + assistant
            conversation.last_message_at = timezone.now()
            conversation.save()
            
            return Response({
                "user_message": AIMessageSerializer(user_msg).data,
                "assistant_message": AIMessageSerializer(assistant_msg).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"AI generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIVoiceChatView(APIView):
    """Voice input/output for AI tutor"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request, conversation_id):
        """
        Process voice input and return voice response
        
        Request body:
            {
                "audio": "base64_encoded_audio_data",
                "format": "webm" or "mp3"
            }
        
        Returns:
            {
                "transcript": str,
                "response_text": str,
                "response_audio": "base64_encoded_audio"
            }
        """
        audio_data = request.data.get('audio')
        audio_format = request.data.get('format', 'webm')
        
        if not audio_data:
            return Response(
                {"error": "Audio data required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation = AIConversation.objects.get(
                id=conversation_id,
                student=request.user,
                is_active=True
            )
        except AIConversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"audio.{audio_format}"
            
            # Speech-to-Text
            transcript_result = SpeechService.transcribe_audio(audio_file)
            user_text = transcript_result['text']
            
            # Save user message with audio
            user_msg = AIMessage.objects.create(
                conversation=conversation,
                role='user',
                content=user_text,
                has_audio=True,
                audio_duration_seconds=transcript_result.get('duration', 0)
            )
            user_msg.audio_file.save(f"user_{user_msg.id}.{audio_format}", ContentFile(audio_bytes))
            
            # Get AI response (text)
            context = ConversationManager.get_context_messages(conversation_id)
            context.append({"role": "user", "content": user_text})
            
            response_data = LLMService.generate_response(
                messages=context,
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = response_data['content']
            
            # Text-to-Speech
            response_audio_bytes = SpeechService.synthesize_speech(response_text)
            
            # Save assistant message with audio
            assistant_msg = AIMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=response_text,
                model_used=response_data['model'],
                tokens_used=response_data['tokens'],
                response_time_ms=response_data['time_ms'],
                has_audio=True
            )
            assistant_msg.audio_file.save(
                f"assistant_{assistant_msg.id}.mp3",
                ContentFile(response_audio_bytes)
            )
            
            # Update conversation
            conversation.message_count += 2
            conversation.last_message_at = timezone.now()
            conversation.save()
            
            # Encode response audio to base64
            response_audio_b64 = base64.b64encode(response_audio_bytes).decode('utf-8')
            
            return Response({
                "transcript": user_text,
                "response_text": response_text,
                "response_audio": response_audio_b64,
                "user_message_id": user_msg.id,
                "assistant_message_id": assistant_msg.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Voice processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIMessageListView(generics.ListAPIView):
    """Get conversation message history"""
    serializer_class = AIMessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        return AIMessage.objects.filter(
            conversation_id=conversation_id,
            conversation__student=self.request.user
        ).order_by('created_at')


class AIFeedbackView(generics.CreateAPIView):
    """Submit feedback on AI response"""
    serializer_class = AIFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)
