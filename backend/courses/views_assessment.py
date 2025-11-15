from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from accounts.permissions import IsStudent, IsTeacher
from .models import (
    MockTest, MockTestQuestion, MockTestAttempt, MockTestAnswer,
    Session, SessionSummary, StudentProgressAnalytics, RecommendedCourse
)
from .serializers import (
    MockTestSerializer, MockTestAttemptSerializer, MockTestAnswerSerializer,
    SessionSummarySerializer, StudentProgressAnalyticsSerializer,
    RecommendedCourseSerializer
)
from .assesment_services import AssessmentGenerator, SessionSummarizer
from .pdf_service import ScorecardGenerator
from .ml_service import RecommendationEngine


class GenerateMockTestView(APIView):
    """AI-generate mock test from session content"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, session_id):
        try:
            session = Session.objects.get(
                id=session_id,
                student=request.user
            )
        except Session.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        
        # Extract content from session
        content = SessionSummarizer.extract_transcript_from_session(session_id)
        
        if not content:
            return Response(
                {'error': 'No content available to generate test from'},
                status=400
            )
        
        difficulty = request.data.get('difficulty', 'MEDIUM')
        num_questions = int(request.data.get('num_questions', 10))
        
        try:
            # Generate test
            test_data = AssessmentGenerator.generate_test_from_content(
                content=content,
                subject=session.course.title if session.course else "General",
                difficulty=difficulty,
                num_questions=num_questions
            )
            
            # Save to database
            with transaction.atomic():
                mock_test = MockTest.objects.create(
                    session=session,
                    course=session.course,
                    student=request.user,
                    title=test_data.get('title', f"Test for {session.title}"),
                    description=test_data.get('description', ''),
                    subject=session.course.title if session.course else "General",
                    difficulty=difficulty,
                    total_questions=num_questions,
                    generated_from_content=content[:500],
                    ai_prompt="Generated from session content"
                )
                
                # Create questions
                for idx, q_data in enumerate(test_data.get('questions', [])):
                    MockTestQuestion.objects.create(
                        mock_test=mock_test,
                        order=idx,
                        question_type=q_data.get('question_type', 'MCQ'),
                        question_text=q_data.get('question_text', ''),
                        options=q_data.get('options', []),
                        correct_answer=q_data.get('correct_answer', ''),
                        explanation=q_data.get('explanation', ''),
                        bloom_level=q_data.get('bloom_level', ''),
                        points=q_data.get('points', 1.0)
                    )
            
            return Response(
                MockTestSerializer(mock_test).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': f'Test generation failed: {str(e)}'},
                status=500
            )


class MockTestListView(generics.ListAPIView):
    """List available mock tests for student"""
    serializer_class = MockTestSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        return MockTest.objects.filter(
            student=self.request.user,
            is_published=True
        ).prefetch_related('questions')


class StartMockTestView(APIView):
    """Start a new mock test attempt"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request, test_id):
        try:
            mock_test = MockTest.objects.get(
                id=test_id,
                student=request.user,
                is_published=True
            )
        except MockTest.DoesNotExist:
            return Response({'error': 'Test not found'}, status=404)
        
        # Create attempt
        max_score = sum(q.points for q in mock_test.questions.all())
        
        attempt = MockTestAttempt.objects.create(
            mock_test=mock_test,
            student=request.user,
            status='IN_PROGRESS',
            max_score=max_score
        )
        
        return Response(
            MockTestAttemptSerializer(attempt).data,
            status=status.HTTP_201_CREATED
        )


class SubmitMockTestView(APIView):
    """Submit answers and get results"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request, attempt_id):
        try:
            attempt = MockTestAttempt.objects.get(
                id=attempt_id,
                student=request.user,
                status='IN_PROGRESS'
            )
        except MockTestAttempt.DoesNotExist:
            return Response({'error': 'Attempt not found'}, status=404)
        
        answers_data = request.data.get('answers', [])
        # Expected format: [{"question_id": 1, "selected_answer": "A"}, ...]
        
        total_score = 0.0
        
        with transaction.atomic():
            for ans_data in answers_data:
                question_id = ans_data.get('question_id')
                selected = ans_data.get('selected_answer')
                
                try:
                    question = MockTestQuestion.objects.get(
                        id=question_id,
                        mock_test=attempt.mock_test
                    )
                except MockTestQuestion.DoesNotExist:
                    continue
                
                # Check correctness
                is_correct = False
                points_earned = 0.0
                
                if question.question_type == 'MCQ':
                    is_correct = (selected.strip().upper() == question.correct_answer.strip().upper())
                    points_earned = question.points if is_correct else 0.0
                elif question.question_type == 'SHORT_ANSWER':
                    # Use AI to evaluate
                    eval_result = AssessmentGenerator.evaluate_short_answer(
                        question=question.question_text,
                        correct_answer=question.correct_answer,
                        student_answer=selected
                    )
                    is_correct = eval_result.get('is_correct', False)
                    points_earned = question.points * eval_result.get('score', 0.0)
                
                # Save answer
                MockTestAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_answer=selected,
                    is_correct=is_correct,
                    points_earned=points_earned
                )
                
                total_score += points_earned
            
            # Update attempt
            attempt.total_score = total_score
            attempt.percentage = (total_score / attempt.max_score * 100) if attempt.max_score > 0 else 0
            attempt.passed = attempt.percentage >= attempt.mock_test.passing_score
            attempt.submitted_at = timezone.now()
            attempt.time_taken_minutes = int((timezone.now() - attempt.started_at).total_seconds() / 60)
            attempt.status = 'COMPLETED'
            attempt.save()
            
            # Generate PDF scorecard
            try:
                ScorecardGenerator.save_scorecard_to_attempt(attempt)
            except Exception as e:
                print(f"PDF generation failed: {e}")
        
        return Response(
            MockTestAttemptSerializer(attempt).data,
            status=status.HTTP_200_OK
        )


class MockTestAttemptListView(generics.ListAPIView):
    """List student's test attempts"""
    serializer_class = MockTestAttemptSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        return MockTestAttempt.objects.filter(
            student=self.request.user
        ).select_related('mock_test').order_by('-started_at')


class GenerateSessionSummaryView(APIView):
    """AI-generate summary for completed session"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, session_id):
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        
        # Check permissions
        if request.user.id not in [session.student_id, session.teacher_id]:
            return Response({'error': 'Not authorized'}, status=403)
        
        # Check if already summarized
        if hasattr(session, 'ai_summary'):
            return Response(
                SessionSummarySerializer(session.ai_summary).data,
                status=200
            )
        
        # Extract transcript
        transcript = SessionSummarizer.extract_transcript_from_session(session_id)
        
        if not transcript:
            return Response({'error': 'No content to summarize'}, status=400)
        
        try:
            # Generate summary
            summary_data = SessionSummarizer.summarize_session(
                transcript=transcript,
                session_title=session.title,
                duration_minutes=session.duration_minutes
            )
            
            # Save to database
            summary = SessionSummary.objects.create(
                session=session,
                summary_text=summary_data.get('summary_text', ''),
                key_topics=summary_data.get('key_topics', []),
                action_items=summary_data.get('action_items', []),
                original_transcript=transcript[:5000],
                ai_model_used=settings.LLM_PROVIDER
            )
            
            return Response(
                SessionSummarySerializer(summary).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': f'Summary generation failed: {str(e)}'},
                status=500
            )


class StudentAnalyticsView(APIView):
    """Get ML-computed analytics for student"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get(self, request):
        course_id = request.query_params.get('course_id')
        
        try:
            # Compute fresh analytics
            analytics_data = RecommendationEngine.compute_student_analytics(
                student_id=request.user.id,
                course_id=int(course_id) if course_id else None
            )
            
            # Save to database
            analytics, created = StudentProgressAnalytics.objects.update_or_create(
                student=request.user,
                course_id=course_id if course_id else None,
                defaults=analytics_data
            )
            
            return Response(
                StudentProgressAnalyticsSerializer(analytics).data,
                status=200
            )
            
        except Exception as e:
            return Response(
                {'error': f'Analytics computation failed: {str(e)}'},
                status=500
            )


class CourseRecommendationsView(APIView):
    """Get personalized course recommendations"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get(self, request):
        try:
            recommendations = RecommendationEngine.recommend_courses(
                student_id=request.user.id,
                limit=5
            )
            
            # Save to database
            RecommendedCourse.objects.filter(student=request.user).delete()
            
            for idx, rec in enumerate(recommendations):
                RecommendedCourse.objects.create(
                    student=request.user,
                    course=rec['course'],
                    confidence_score=rec['confidence'],
                    reason=rec['reason'],
                    rank=idx
                )
            
            # Serialize and return
            saved_recs = RecommendedCourse.objects.filter(student=request.user).select_related('course')
            
            return Response(
                RecommendedCourseSerializer(saved_recs, many=True).data,
                status=200
            )
            
        except Exception as e:
            return Response(
                {'error': f'Recommendations failed: {str(e)}'},
                status=500
            )
