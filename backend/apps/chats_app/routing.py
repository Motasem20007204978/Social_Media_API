from django.urls import re_path
from .consumers import ChatConsumer


chats_urlpatterns = [
    re_path(
        r"^api/chat/(?P<room_name>[\w-]+)$",
        ChatConsumer.as_asgi(),
        name="websocket-chat",
    )
]
