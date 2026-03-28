"""
ASGI config for VideoVault project.
Supports HTTP and WebSocket protocols via Django Channels.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

# Import after Django setup so models are loaded
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402
from apps.streaming.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    }
)
