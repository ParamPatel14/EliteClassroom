from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from accounts.permissions import IsStudent, IsTeacher
from accounts.models import User
from .models import Session
from .rtc import videosdk_create_or_get_room, videosdk_generate_token
import hmac
import hashlib
import json

class SessionJoinTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        try:
            sess = Session.objects.select_related('student', 'teacher').get(id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        user = request.user
        if user.id not in [sess.student_id, sess.teacher_id]:
            return Response({'error': 'Not allowed'}, status=403)
        if sess.status not in ['PENDING','CONFIRMED']:
            return Response({'error': 'Session not joinable'}, status=400)

        # Create room if needed
        if not sess.provider_room_id:
            room_id = videosdk_create_or_get_room()
            sess.provider_room_id = room_id
            sess.save()
        else:
            room_id = sess.provider_room_id

        role = 'teacher' if user.id == sess.teacher_id else 'student'
        token = videosdk_generate_token(participant_id=str(user.id), room_id=room_id, role=role)
        return Response({'roomId': room_id, 'token': token}, status=200)


class SessionRecordingWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Optionally verify signature if provider sends one
        # signature = request.headers.get('x-videosdk-signature')
        # secret = settings.VIDEOSDK_WEBHOOK_SECRET or ''
        # expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
        # if not hmac.compare_digest(signature or '', expected):
        #     return Response(status=401)

        data = request.data
        # Expected payload: { "event": "recording.completed", "roomId": "...", "assets": [url,...] , "sessionId": <your mapping if provided>}
        event = data.get('event')
        room_id = data.get('roomId')
        assets = data.get('assets', [])

        if event == 'recording.completed' and room_id:
            sess = Session.objects.filter(provider_room_id=room_id).first()
            if sess:
                sess.recording_assets = list(set((sess.recording_assets or []) + assets))
                sess.ended_at = timezone.now()
                sess.save()
        return Response(status=200)
