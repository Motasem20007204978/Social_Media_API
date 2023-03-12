from django.urls import re_path
from .consumers import NotificationConsumer


notifs_urlpatterns = [
    re_path(
        r"^api/notifs/me$",
        NotificationConsumer.as_asgi(),
        name="websocket-notif",
    )
]
