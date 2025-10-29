"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from courses.consumers import WhiteboardConsumer
from django.contrib.auth.middleware import AuthenticationMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django_asgi_app = get_asgi_application()

websocket_urlpatterns = [
    path('ws/whiteboard/<int:session_id>/', WhiteboardConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
  "http": django_asgi_app,
  "websocket": URLRouter(websocket_urlpatterns),
})

from courses.consumers import WhiteboardConsumer, ChatConsumer

websocket_urlpatterns = [
    path('ws/whiteboard/<int:session_id>/', WhiteboardConsumer.as_asgi()),
    path('ws/chat/<int:session_id>/', ChatConsumer.as_asgi()),
]

