"""
AI Learning Assistant Service
Handles LLM, STT, and TTS integration
"""

import time
from typing import List, Dict, Optional
from django.conf import settings
import openai
import google.generativeai as genai
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
import io
import base64

# Initialize APIs
if settings.OPENAI_API_KEY:
    openai.api_key = settings.OPENAI_API_KEY

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

if settings.ELEVENLABS_API_KEY:
    set_api_key(settings.ELEVENLABS_API_KEY)


class LLMService:
    """Unified interface for LLM providers"""
    
    @staticmethod
    def generate_response(
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> Dict:
        """
        Generate AI response using configured provider
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            temperature: Creativity level (0.0-1.0)
            max_tokens: Max response length
            stream: Stream response chunks
        
        Returns:
            {"content": str, "model": str, "tokens": int, "time_ms": int}
        """
        start_time = time.time()
        
        if settings.LLM_PROVIDER == 'openai':
            return LLMService._openai_generate(messages, temperature, max_tokens, stream)
        elif settings.LLM_PROVIDER == 'gemini':
            return LLMService._gemini_generate(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")
    
    @staticmethod
    def _openai_generate(messages, temperature, max_tokens, stream):
        """Generate with OpenAI GPT-4"""
        start = time.time()
        
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        if stream:
            return response  # Return stream object
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        return {
            "content": content,
            "model": "gpt-4-turbo",
            "tokens": tokens,
            "time_ms": int((time.time() - start) * 1000)
        }
    
    @staticmethod
    def _gemini_generate(messages, temperature, max_tokens):
        """Generate with Google Gemini"""
        start = time.time()
        
        # Convert messages to Gemini format
        model = genai.GenerativeModel('gemini-pro')
        
        # Build conversation history
        history = []
        user_msg = ""
        
        for msg in messages:
            if msg['role'] == 'system':
                # Gemini doesn't have system role, prepend to first user message
                continue
            elif msg['role'] == 'user':
                user_msg = msg['content']
            elif msg['role'] == 'assistant':
                history.append({
                    "role": "user",
                    "parts": [user_msg]
                })
                history.append({
                    "role": "model",
                    "parts": [msg['content']]
                })
        
        # Get system prompt if exists
        system_prompt = next((m['content'] for m in messages if m['role'] == 'system'), "")
        if system_prompt:
            user_msg = f"{system_prompt}\n\n{user_msg}"
        
        chat = model.start_chat(history=history[:-1] if history else [])
        response = chat.send_message(
            user_msg,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        
        return {
            "content": response.text,
            "model": "gemini-pro",
            "tokens": len(response.text.split()),  # Approximate
            "time_ms": int((time.time() - start) * 1000)
        }
    
    @staticmethod
    def create_system_prompt(student_name: str, subject: str, goal: str = "") -> str:
        """Generate contextual system prompt for tutoring"""
        
        base = f"""You are an expert AI tutor helping {student_name} learn {subject}.

Your role:
- Explain concepts clearly with examples
- Ask guiding questions to deepen understanding
- Provide step-by-step solutions
- Encourage critical thinking
- Be patient and supportive
- Adapt explanations to the student's level

Communication style:
- Conversational and friendly
- Use analogies and real-world examples
- Break complex topics into simple steps
- Check for understanding regularly
"""
        
        if goal:
            base += f"\nStudent's goal: {goal}\n"
        
        base += "\nAlways prioritize clarity and pedagogical effectiveness."
        
        return base


class SpeechService:
    """Speech-to-Text and Text-to-Speech"""
    
    @staticmethod
    def transcribe_audio(audio_file) -> Dict:
        """
        Convert speech to text using Whisper
        
        Args:
            audio_file: File object or path
        
        Returns:
            {"text": str, "duration": float, "language": str}
        """
        start = time.time()
        
        # OpenAI Whisper API
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
        
        return {
            "text": transcript.text,
            "duration": transcript.duration,
            "language": transcript.language,
            "time_ms": int((time.time() - start) * 1000)
        }
    
    @staticmethod
    def synthesize_speech(text: str, voice_id: str = None) -> bytes:
        """
        Convert text to speech using ElevenLabs
        
        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID
        
        Returns:
            Audio bytes (MP3)
        """
        if not voice_id:
            voice_id = settings.ELEVENLABS_VOICE_ID
        
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            ),
            model="eleven_monolingual_v1"
        )
        
        return audio


class ConversationManager:
    """Manage AI conversation context"""
    
    @staticmethod
    def get_context_messages(conversation_id: int, limit: int = None) -> List[Dict]:
        """
        Retrieve conversation history for LLM context
        
        Args:
            conversation_id: AIConversation ID
            limit: Max messages (defaults to AI_MAX_CONTEXT_MESSAGES)
        
        Returns:
            List of {"role": str, "content": str}
        """
        from .models import AIConversation, AIMessage
        
        if limit is None:
            limit = settings.AI_MAX_CONTEXT_MESSAGES
        
        conversation = AIConversation.objects.get(id=conversation_id)
        messages = conversation.messages.order_by('-created_at')[:limit]
        
        # Reverse to chronological order
        context = []
        
        # Add system prompt first
        if conversation.system_prompt:
            context.append({
                "role": "system",
                "content": conversation.system_prompt
            })
        
        # Add conversation history
        for msg in reversed(messages):
            if msg.role in ['user', 'assistant']:
                context.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return context
    
    @staticmethod
    def summarize_context(messages: List[Dict]) -> str:
        """
        Summarize long conversations to fit context window
        (Optional: for very long conversations)
        """
        # Simple truncation for now
        # TODO: Implement LLM-based summarization if needed
        return ""
