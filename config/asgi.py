"""
ASGI configuration for CodeView.

Handles:
1. HTTP requests using Django.
2. WebSocket connections using Django Channels.
3. Authentication for WebSocket connections.
"""

import os

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack


# ==========================================
# 1. CONFIGURE DJANGO SETTINGS
# ==========================================

# Tell Django which settings file to use.
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)


# ==========================================
# 2. INITIALIZE DJANGO
# ==========================================

# Initialize Django before importing WebSocket routes
# that may use Django models.
django_asgi_app = get_asgi_application()


# ==========================================
# 3. IMPORT WEBSOCKET ROUTES
# ==========================================

# This file will contain our Group Chat WebSocket URLs.
# We will create it in the next step.
from community.routing import websocket_urlpatterns


# ==========================================
# 4. CONFIGURE ASGI APPLICATION
# ==========================================

application = ProtocolTypeRouter({

    # Handle normal website requests.
    "http": django_asgi_app,

    # Handle real-time WebSocket connections.
    "websocket": AuthMiddlewareStack(

        URLRouter(
            websocket_urlpatterns
        )

    ),

})