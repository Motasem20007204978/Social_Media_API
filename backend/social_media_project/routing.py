from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from auth_app.ws_middlewares import WebSocketJWTAuthMiddleware
from notifications_app.routing import notifs_urlpatterns
from chats_app.routing import chats_urlpatterns


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": WebSocketJWTAuthMiddleware(
            URLRouter(notifs_urlpatterns + chats_urlpatterns)
        ),
    }
)
