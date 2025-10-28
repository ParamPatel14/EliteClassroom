import time
import hmac
import hashlib
import base64
import json
import requests
from django.conf import settings

def videosdk_create_or_get_room():
    url = "https://api.videosdk.live/v2/rooms"
    headers = {
        "Authorization": settings.VIDEOSDK_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"region": settings.VIDEOSDK_REGION}
    res = requests.post(url, headers=headers, json=payload, timeout=10)
    res.raise_for_status()
    data = res.json()
    return data.get("roomId")

def videosdk_generate_token(participant_id: str, room_id: str, role: str, exp_seconds=120):
    """
    Generate a simple auth token usable by client SDK.
    For production, prefer provider-recommended signing strategy.
    """
    # For VideoSDK, direct API key usage works for client initialization;
    # Or you can implement a signed JWT style token if offered.
    # Here we return API key + room/role metadata; client SDK will use API key.
    return {
        "apiKey": settings.VIDEOSDK_API_KEY,
        "roomId": room_id,
        "participantId": participant_id,
        "role": role,
        "expiresIn": exp_seconds
    }
