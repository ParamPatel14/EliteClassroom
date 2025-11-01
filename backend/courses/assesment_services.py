"""
AI-powered assessment generation and scoring
"""

from typing import List, Dict, Optional
from django.conf import settings
import json
from .ai_service import LLMService


class AssessmentGenerator:
    """Generate mock tests from session content"""
    
    @staticmethod
    def generate_test_from_content(
        content: str,
        subject: str,
        difficulty: str = 'MEDIUM',
        num_questions: int = 10
    ) -> Dict:
        """
        Generate a complete mock test from learning content
        
        Args:
            content: Session transcript or learning material
            subject: Subject area
            difficulty: EASY, MEDIUM, or HARD
            num_questions: Number of questions to generate
        
        Returns:
            {
                "title": str,
                "description": str,
                "questions": [
                    {
                        "question_text": str,
                        "question_type": "MCQ",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "B",
                        "explanation": str,
                        "bloom_level": str,
                        "points": float
                    },
                    ...
                ]
            }
        """
        
        prompt = f"""You are an expert educator creating a {difficulty} difficulty assessment.

Subject: {subject}
Number of questions: {num_questions}

Content to base questions on:
{content[:3000]}  # Limit context

Generate a comprehensive {num_questions}-question test with:
- Mix of question types (Multiple Choice, True/False)
- Aligned with Bloom's Taxonomy (Remember, Understand, Apply, Analyze)
- Clear explanations for each answer
- Progressive difficulty

Return ONLY valid JSON in this exact format:
{{
  "title": "Test title",
  "description": "Brief test description",
  "questions": [
    {{
      "question_text": "Question here?",
      "question_type": "MCQ",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "A",
      "explanation": "Why A is correct",
      "bloom_level": "understand",
      "points": 1.0
    }}
  ]
}}
"""
        
        messages = [
            {"role": "system", "content": "You are an expert test generator. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = LLMService.generate_response(
            messages=messages,
            temperature=0.3,  # Lower temp for more consistent output
            max_tokens=2000
        )
        
        # Parse JSON response
        try:
            # Clean markdown code blocks if present
            content = response.get('content', '') if isinstance(response, dict) else str(response)
            # If content wrapped in ```json ... ``` or ``` ... ```
            if '```json' in content:
                # Extract text between ```json and the next ```
                try:
                    content = content.split('```json', 1)[1].split('```', 1)[0]
                except Exception:
                    # Fall back to removing leading fence
                    content = content.split('```json', 1)[-1]
            elif '```' in content:
                try:
                    content = content.split('```', 1)[1].split('```', 1)[0]
                except Exception:
                    content = content.split('```', 1)[-1]
            
            test_data = json.loads(content.strip())
            return test_data
        except json.JSONDecodeError as e:
            # Fallback: try to extract JSON from response
            print(f"JSON parse error: {e}")
            print(f"Response: {response.get('content') if isinstance(response, dict) else response}")
            raise ValueError("Failed to generate valid test format")
    
    @staticmethod
    def evaluate_short_answer(
        question: str,
        correct_answer: str,
        student_answer: str
    ) -> Dict:
        """
        Use LLM to evaluate subjective/short answers
        
        Returns:
            {
                "is_correct": bool,
                "score": float (0-1),
                "feedback": str
            }
        """
        
        prompt = f"""Evaluate this student's answer:

Question: {question}
Expected Answer: {correct_answer}
Student Answer: {student_answer}

Provide:
1. Score (0.0 to 1.0)
2. Whether essentially correct (yes/no)
3. Brief feedback

Return JSON:
{{
  "score": 0.85,
  "is_correct": true,
  "feedback": "Good answer, but could mention..."
}}
"""
        
        messages = [
            {"role": "system", "content": "You are an expert grader. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = LLMService.generate_response(messages=messages, temperature=0.2, max_tokens=300)
        
        try:
            # Safely get content string from response (it may be a dict or raw string)
            content = response.get('content', '') if isinstance(response, dict) else str(response)

            # Remove fenced code blocks if present (```json or ``` ... ```)
            if '```json' in content:
                try:
                    content = content.split('```json', 1)[1].split('```', 1)[0]
                except Exception:
                    content = content.split('```json', 1)[-1]
            elif '```' in content:
                try:
                    content = content.split('```', 1)[1].split('```', 1)[0]
                except Exception:
                    content = content.split('```', 1)[-1]

            result = json.loads(content.strip())
            return result
        except Exception:
            return {"score": 0.5, "is_correct": False, "feedback": "Unable to evaluate"}


class SessionSummarizer:
    """Generate summaries from session transcripts"""
    
    @staticmethod
    def summarize_session(
        transcript: str,
        session_title: str,
        duration_minutes: int
    ) -> Dict:
        """
        Generate structured summary from session content
        
        Returns:
            {
                "summary_text": str,
                "key_topics": [str],
                "action_items": [str],
                "questions_discussed": [str]
            }
        """
        
        prompt = f"""Summarize this tutoring session:

Session: {session_title}
Duration: {duration_minutes} minutes

Transcript:
{transcript[:4000]}

Provide:
1. Concise summary (2-3 paragraphs)
2. Key topics covered (bullet points)
3. Action items for student
4. Main questions discussed

Return JSON:
{{
  "summary_text": "Overall summary...",
  "key_topics": ["Topic 1", "Topic 2", "Topic 3"],
  "action_items": ["Action 1", "Action 2"],
  "questions_discussed": ["Question 1", "Question 2"]
}}
"""
        
        messages = [
            {"role": "system", "content": "You are an expert educational summarizer. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = LLMService.generate_response(messages=messages, temperature=0.3, max_tokens=1000)
        
        try:
            content = response['content']
            if '```json' in content:
                content = content.split('``````')[0]
            
            summary = json.loads(content.strip())
            return summary
        except:
            return {
                "summary_text": "Session completed successfully.",
                "key_topics": [],
                "action_items": [],
                "questions_discussed": []
            }
    
    @staticmethod
    def extract_transcript_from_session(session_id: int) -> str:
        """
        Extract text from session messages/chat for summarization
        """
        from .models import SessionMessage, Session
        
        try:
            session = Session.objects.get(id=session_id)
            messages = SessionMessage.objects.filter(session=session).order_by('sent_at')
            
            transcript = f"Session: {session.title}\n\n"
            for msg in messages:
                role = "Teacher" if msg.sender.role == 'TEACHER' else "Student"
                transcript += f"{role}: {msg.text}\n"
            
            return transcript
        except:
            return ""
