"""
CodeView — WebSocket URL Routing.

This file connects WebSocket URLs to their
corresponding Django Channels consumers.

Example:
ws://127.0.0.1:8000/ws/groups/4/chat/
"""

from django.urls import re_path

from . import consumers


# ==========================================
# GROUP CHAT WEBSOCKET ROUTES
# ==========================================

websocket_urlpatterns = [

    # Connect developers to a specific group's chat.
    re_path(
        r"^ws/groups/(?P<group_id>\d+)/chat/$",
        consumers.GroupChatConsumer.as_asgi(),
    ),

]