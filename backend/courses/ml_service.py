"""
Machine Learning recommendation engine
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from typing import List, Dict
from django.db.models import Avg, Count, Q, Sum
from datetime import datetime, timedelta


class RecommendationEngine:
    """ML-powered course and learning recommendations"""
    
    @staticmethod
    def compute_student_analytics(student_id: int, course_id: int = None):
        """
        Compute comprehensive analytics for a student
        
        Returns StudentProgressAnalytics data dict
        """
        from .models import (
            User, Course, Session, MockTestAttempt, ModuleProgress,
            Enrollment, StudentProgressAnalytics
        )
        
        student = User.objects.get(id=student_id)
        
        # Filter by course if provided
        sessions_qs = Session.objects.filter(student=student)
        attempts_qs = MockTestAttempt.objects.filter(student=student)
        enrollments_qs = Enrollment.objects.filter(student=student)
        
        if course_id:
            sessions_qs = sessions_qs.filter(course_id=course_id)
            attempts_qs = attempts_qs.filter(mock_test__course_id=course_id)
            enrollments_qs = enrollments_qs.filter(course_id=course_id)
        
        # Aggregate metrics
        total_sessions = sessions_qs.filter(status='COMPLETED').count()
        total_attempts = attempts_qs.filter(status='COMPLETED').count()
        avg_score = attempts_qs.filter(status='COMPLETED').aggregate(
            avg=Avg('percentage')
        )['avg'] or 0.0
        
        # Module completion
        if course_id:
            progress_qs = ModuleProgress.objects.filter(
                enrollment__student=student,
                enrollment__course_id=course_id
            )
            modules_completed = progress_qs.filter(is_completed=True).count()
            modules_in_progress = progress_qs.filter(is_started=True, is_completed=False).count()
            total_modules = progress_qs.count()
            completion_rate = (modules_completed / total_modules * 100) if total_modules > 0 else 0.0
        else:
            modules_completed = ModuleProgress.objects.filter(
                enrollment__student=student,
                is_completed=True
            ).count()
            modules_in_progress = ModuleProgress.objects.filter(
                enrollment__student=student,
                is_started=True,
                is_completed=False
            ).count()
            completion_rate = 0.0
        
        # Learning hours
        total_minutes = sessions_qs.aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        total_hours = total_minutes / 60.0
        avg_duration = sessions_qs.aggregate(
            avg=Avg('duration_minutes')
        )['avg'] or 0.0
        
        # Last activity
        last_session = sessions_qs.order_by('-scheduled_date').first()
        last_activity = last_session.scheduled_date if last_session else None
        
        # Strengths and weaknesses (from test results)
        strengths, weaknesses = RecommendationEngine._analyze_strengths_weaknesses(
            student_id, course_id
        )
        
        # Learning pace
        pace = RecommendationEngine._calculate_learning_pace(student_id, course_id)
        
        # Dropout risk
        dropout_risk = RecommendationEngine._calculate_dropout_risk(
            student_id, last_activity, completion_rate, avg_score
        )
        
        # Recommended topics
        recommended_topics = RecommendationEngine._recommend_next_topics(
            student_id, weaknesses, course_id
        )
        
        # Predicted completion
        predicted_date = RecommendationEngine._predict_completion_date(
            student_id, course_id, completion_rate, pace
        )
        
        analytics_data = {
            'student_id': student_id,
            'course_id': course_id,
            'total_sessions': total_sessions,
            'total_test_attempts': total_attempts,
            'average_test_score': round(avg_score, 2),
            'modules_completed': modules_completed,
            'modules_in_progress': modules_in_progress,
            'completion_rate': round(completion_rate, 2),
            'total_learning_hours': round(total_hours, 2),
            'avg_session_duration_minutes': round(avg_duration, 2),
            'last_activity_date': last_activity,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommended_topics': recommended_topics,
            'learning_pace': pace,
            'predicted_completion_date': predicted_date,
            'at_risk_of_dropout': dropout_risk > 60,
            'dropout_risk_score': round(dropout_risk, 2),
        }
        
        return analytics_data
    
    @staticmethod
    def _analyze_strengths_weaknesses(student_id, course_id):
        """Analyze test performance by topic"""
        from .models import MockTestAnswer, MockTestAttempt
        
        attempts = MockTestAttempt.objects.filter(
            student_id=student_id,
            status='COMPLETED'
        )
        if course_id:
            attempts = attempts.filter(mock_test__course_id=course_id)
        
        # Group answers by bloom level/topic
        topic_scores = {}
        
        for attempt in attempts:
            for answer in attempt.answers.select_related('question'):
                topic = answer.question.bloom_level or 'General'
                if topic not in topic_scores:
                    topic_scores[topic] = {'correct': 0, 'total': 0}
                
                topic_scores[topic]['total'] += 1
                if answer.is_correct:
                    topic_scores[topic]['correct'] += 1
        
        # Calculate accuracy per topic
        topic_accuracy = {
            topic: (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            for topic, data in topic_scores.items()
        }
        
        # Strengths: > 75%
        strengths = [topic for topic, acc in topic_accuracy.items() if acc >= 75]
        # Weaknesses: < 60%
        weaknesses = [topic for topic, acc in topic_accuracy.items() if acc < 60]
        
        return strengths[:5], weaknesses[:5]
    
    @staticmethod
    def _calculate_learning_pace(student_id, course_id):
        """Determine if student is learning SLOW, MODERATE, or FAST"""
        from .models import ModuleProgress
        
        if not course_id:
            return 'MODERATE'
        
        progress = ModuleProgress.objects.filter(
            enrollment__student_id=student_id,
            enrollment__course_id=course_id,
            is_completed=True
        )
        
        if not progress.exists():
            return 'MODERATE'
        
        # Calculate average time per module
        avg_time = progress.aggregate(
            avg=Avg('time_spent_minutes')
        )['avg'] or 0
        
        # Compare to expected (e.g., estimated_hours * 60)
        # Simple heuristic: < 50% of estimated = FAST, > 150% = SLOW
        if avg_time < 30:
            return 'FAST'
        elif avg_time > 90:
            return 'SLOW'
        else:
            return 'MODERATE'
    
    @staticmethod
    def _calculate_dropout_risk(student_id, last_activity, completion_rate, avg_score):
        """Calculate dropout risk score (0-100)"""
        risk = 0.0
        
        # Factor 1: Inactivity (40% weight)
        if last_activity:
            days_since = (datetime.now().date() - last_activity).days
            if days_since > 30:
                risk += 40
            elif days_since > 14:
                risk += 25
            elif days_since > 7:
                risk += 10
        else:
            risk += 40
        
        # Factor 2: Low completion rate (30% weight)
        if completion_rate < 20:
            risk += 30
        elif completion_rate < 40:
            risk += 15
        
        # Factor 3: Low test scores (30% weight)
        if avg_score < 50:
            risk += 30
        elif avg_score < 70:
            risk += 15
        
        return min(risk, 100.0)
    
    @staticmethod
    def _recommend_next_topics(student_id, weaknesses, course_id):
        """Recommend next topics to study based on weaknesses and prerequisites"""
        # Simple heuristic: prioritize weaknesses
        recommendations = weaknesses[:3]
        
        # TODO: Add prerequisite-based recommendations from course modules
        
        return recommendations
    
    @staticmethod
    def _predict_completion_date(student_id, course_id, completion_rate, pace):
        """Predict course completion date"""
        if not course_id or completion_rate == 0:
            return None
        
        # Estimate remaining time based on pace
        pace_multipliers = {'FAST': 0.7, 'MODERATE': 1.0, 'SLOW': 1.5}
        multiplier = pace_multipliers.get(pace, 1.0)
        
        # Assume 10 weeks baseline * (100 - completion_rate) / 100
        remaining_weeks = (100 - completion_rate) / 10 * multiplier
        
        predicted = datetime.now().date() + timedelta(weeks=remaining_weeks)
        return predicted
    
    @staticmethod
    def recommend_courses(student_id: int, limit: int = 5) -> List[Dict]:
        """
        Generate personalized course recommendations
        
        Returns list of:
            {
                "course_id": int,
                "confidence": float,
                "reason": str
            }
        """
        from .models import Course, Enrollment, StudentProgressAnalytics, User
        
        student = User.objects.get(id=student_id)
        student_profile = getattr(student, 'student_profile', None)
        
        # Get enrolled courses (exclude)
        enrolled_ids = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
        
        # Get analytics
        analytics = StudentProgressAnalytics.objects.filter(student=student).first()
        
        # Candidate courses
        courses = Course.objects.filter(is_active=True).exclude(id__in=enrolled_ids)
        
        recommendations = []
        
        for course in courses:
            confidence = 0.0
            reasons = []
            
            # Factor 1: Subject interest match (30%)
            if student_profile and course.category in (student_profile.subjects_interested or []):
                confidence += 30
                reasons.append(f"Matches your interest in {course.category}")
            
            # Factor 2: Difficulty alignment (20%)
            if analytics:
                if analytics.average_test_score >= 80 and course.level == 'ADVANCED':
                    confidence += 20
                    reasons.append("Your strong performance suggests you're ready for advanced content")
                elif analytics.average_test_score < 70 and course.level == 'BEGINNER':
                    confidence += 20
                    reasons.append("Foundation course to strengthen basics")
            
            # Factor 3: Learning pace compatibility (20%)
            if analytics and analytics.learning_pace == 'FAST' and course.duration_weeks <= 8:
                confidence += 20
                reasons.append("Short duration matches your fast learning pace")
            elif analytics and analytics.learning_pace == 'SLOW' and course.duration_weeks >= 12:
                confidence += 20
                reasons.append("Extended timeline suits your thorough learning style")
            
            # Factor 4: Teacher rating (15%)
            if course.teacher.teacher_profile.average_rating >= 4.5:
                confidence += 15
                reasons.append(f"Highly-rated instructor ({course.teacher.teacher_profile.average_rating}★)")
            
            # Factor 5: Popularity (15%)
            enrollment_count = course.enrollments.count()
            if enrollment_count >= 10:
                confidence += 15
                reasons.append(f"Popular course with {enrollment_count} students")
            
            if confidence > 0:
                recommendations.append({
                    'course': course,
                    'confidence': min(confidence, 100.0),
                    'reason': ' • '.join(reasons)
                })
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return recommendations[:limit]
