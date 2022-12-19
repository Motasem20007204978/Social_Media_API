from channels.routing import ProtocolTypeRouter, URLRouter
from apps.notifications_app.routing import websocket_urlpatterns
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
