from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Corrected pattern for your ChatConsumer
    re_path(r'^/?ws/chat/(?P<room_name>[0-9a-fA-F-]+)/$', consumers.ChatConsumer.as_asgi()),
]
