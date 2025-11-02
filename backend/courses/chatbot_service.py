"""
Intelligent support chatbot with semantic search and escalation
"""

from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.db.models import Q
import re
import json
from .ai_service import LLMService


class KnowledgeBase:
    """Semantic search over FAQ knowledge base"""
    
    @staticmethod
    def search_faqs(query: str, category: str = None, limit: int = 3) -> List[Dict]:
        """
        Search FAQs using keyword matching and semantic similarity
        
        Returns:
            List of {"faq": SupportFAQ, "score": float}
        """
        from .models import SupportFAQ
        
        # Filter by category if provided
        faqs = SupportFAQ.objects.filter(is_active=True)
        if category:
            faqs = faqs.filter(category=category)
        
        # Simple keyword-based scoring
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        results = []
        
        for faq in faqs:
            score = 0.0
            
            # Exact question match (high score)
            if query_lower in faq.question.lower():
                score += 50
            
            # Keyword matches
            faq_text = f"{faq.question} {' '.join(faq.keywords)}".lower()
            matching_words = sum(1 for word in query_words if word in faq_text)
            score += matching_words * 10
            
            # Boost for frequently helpful FAQs
            if faq.helpful_count > 0:
                score += min(faq.helpful_count * 0.5, 20)
            
            if score > 0:
                results.append({
                    'faq': faq,
                    'score': score,
                    'question': faq.question,
                    'answer': faq.answer,
                    'category': faq.category
                })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    @staticmethod
    def get_category_from_query(query: str) -> str:
        """Detect category from user query"""
        query_lower = query.lower()
        
        category_keywords = {
            'ACCOUNT': ['login', 'password', 'register', 'signup', 'account', 'profile', 'email', 'verify'],
            'BOOKING': ['book', 'session', 'schedule', 'appointment', 'teacher', 'class', 'cancel', 'reschedule'],
            'PAYMENT': ['payment', 'pay', 'billing', 'invoice', 'refund', 'credit', 'card', 'price', 'cost'],
            'TECHNICAL': ['error', 'bug', 'not working', 'problem', 'issue', 'crash', 'slow', 'loading'],
            'COURSES': ['course', 'lesson', 'module', 'content', 'video', 'material', 'curriculum'],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return category
        
        return 'GENERAL'


class IntentClassifier:
    """Classify user intent from message"""
    
    INTENTS = {
        'GREETING': ['hello', 'hi', 'hey', 'good morning', 'good evening'],
        'HELP': ['help', 'assist', 'support', 'guide'],
        'THANK': ['thank', 'thanks', 'appreciate', 'grateful'],
        'ESCALATE': ['human', 'agent', 'support team', 'speak to someone', 'real person'],
        'FEEDBACK': ['feedback', 'complaint', 'suggest', 'improve'],
    }
    
    @staticmethod
    def classify(message: str) -> Tuple[str, float]:
        """
        Returns (intent, confidence)
        """
        message_lower = message.lower()
        
        for intent, keywords in IntentClassifier.INTENTS.items():
            if any(keyword in message_lower for keyword in keywords):
                # Simple confidence based on match
                return intent, 0.8
        
        return 'QUERY', 0.6


class ChatbotEngine:
    """Main chatbot logic with LLM fallback"""
    
    @staticmethod
    def generate_response(
        user_message: str,
        conversation_history: List[Dict],
        user_context: Dict = None
    ) -> Dict:
        """
        Generate bot response using hybrid approach:
        1. Intent classification
        2. FAQ search
        3. LLM fallback with context
        
        Returns:
            {
                "response": str,
                "intent": str,
                "confidence": float,
                "faq_matched": int or None,
                "suggested_actions": [str],
                "escalation_suggested": bool
            }
        """
        
        # Classify intent
        intent, confidence = IntentClassifier.classify(user_message)
        
        # Handle greetings
        if intent == 'GREETING':
            greeting = "Hi there! 👋 I'm your Elite Classroom support assistant. How can I help you today?"
            if user_context and user_context.get('name'):
                greeting = f"Hi {user_context['name']}! 👋 How can I assist you today?"
            
            return {
                "response": greeting,
                "intent": intent,
                "confidence": confidence,
                "faq_matched": None,
                "suggested_actions": [
                    "Book a session",
                    "Find a teacher",
                    "Account help",
                    "Payment questions"
                ],
                "escalation_suggested": False
            }
        
        # Handle explicit escalation requests
        if intent == 'ESCALATE':
            return {
                "response": "I'll connect you with our support team. They'll get back to you shortly. Would you like to create a support ticket?",
                "intent": intent,
                "confidence": confidence,
                "faq_matched": None,
                "suggested_actions": ["Create Ticket", "Continue Chatting"],
                "escalation_suggested": True
            }
        
        # Handle thanks
        if intent == 'THANK':
            return {
                "response": "You're welcome! Is there anything else I can help you with?",
                "intent": intent,
                "confidence": confidence,
                "faq_matched": None,
                "suggested_actions": [],
                "escalation_suggested": False
            }
        
        # Search FAQs
        category = KnowledgeBase.get_category_from_query(user_message)
        faq_results = KnowledgeBase.search_faqs(user_message, category=category, limit=3)
        
        if faq_results and faq_results[0]['score'] > 40:
            # High-confidence FAQ match
            best_match = faq_results[0]
            
            response = f"{best_match['answer']}\n\n"
            
            # Add related questions if available
            if len(faq_results) > 1:
                response += "\n**Related questions:**\n"
                for i, result in enumerate(faq_results[1:], 1):
                    response += f"{i}. {result['question']}\n"
            
            return {
                "response": response,
                "intent": "FAQ_MATCH",
                "confidence": min(best_match['score'] / 100, 0.95),
                "faq_matched": best_match['faq'].id,
                "suggested_actions": ["Was this helpful?", "Talk to human"],
                "escalation_suggested": False
            }
        
        # LLM fallback for complex queries
        try:
            llm_response = ChatbotEngine._llm_fallback(
                user_message,
                conversation_history,
                user_context,
                category
            )
            return llm_response
        except Exception as e:
            # Ultimate fallback
            return {
                "response": "I apologize, but I'm having trouble understanding your question. Would you like to speak with our support team?",
                "intent": "ERROR",
                "confidence": 0.0,
                "faq_matched": None,
                "suggested_actions": ["Create Ticket", "Try Again"],
                "escalation_suggested": True
            }
    
    @staticmethod
    def _llm_fallback(
        user_message: str,
        conversation_history: List[Dict],
        user_context: Dict,
        category: str
    ) -> Dict:
        """Use LLM when FAQ search fails"""
        
        # Build context
        context_parts = [
            "You are a helpful support assistant for Elite Classroom, an online tutoring platform.",
            "\nPlatform features:",
            "- Students can find and book teachers",
            "- Live video sessions with whiteboard",
            "- AI tutor for 24/7 help",
            "- Mock tests and progress tracking",
            "- Course enrollments and learning paths",
        ]
        
        if user_context:
            if user_context.get('is_authenticated'):
                context_parts.append(f"\nUser: {user_context.get('name', 'Student')}")
                context_parts.append(f"Role: {user_context.get('role', 'student')}")
        
        context_parts.append(f"\nQuery category: {category}")
        context_parts.append("\nProvide a helpful, concise answer. If you're unsure, suggest contacting support.")
        
        system_prompt = "\n".join(context_parts)
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 5 messages)
        for msg in conversation_history[-5:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        llm_result = LLMService.generate_response(
            messages=messages,
            temperature=0.3,
            max_tokens=300
        )
        
        response_text = llm_result['content']
        
        # Detect if user should be escalated based on response
        escalate_keywords = ['contact support', 'reach out', 'email us', 'cannot help']
        should_escalate = any(keyword in response_text.lower() for keyword in escalate_keywords)
        
        return {
            "response": response_text,
            "intent": "LLM_FALLBACK",
            "confidence": 0.7,
            "faq_matched": None,
            "suggested_actions": ["Helpful?", "Talk to human"] if not should_escalate else ["Create Ticket"],
            "escalation_suggested": should_escalate,
            "model_used": llm_result['model'],
            "tokens_used": llm_result['tokens']
        }
