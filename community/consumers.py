"""
CodeView — Group Chat WebSocket Consumer.

Handles:
1. Connecting developers to a group chat.
2. Checking whether developers belong to the group.
3. Sending real-time events to connected developers.
4. Disconnecting developers from the group.
"""

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from .models import ProjectGroup


class GroupChatConsumer(AsyncJsonWebsocketConsumer):
    """Manage real-time WebSocket connections for group chat."""

    async def connect(self):
        """Connect a developer to their group's chat."""

        # Get the logged-in developer.
        self.user = self.scope["user"]

        # Get the group ID from the WebSocket URL.
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]

        # Create a unique channel-layer group name.
        self.room_group_name = f"group_chat_{self.group_id}"

        # Reject developers who are not logged in.
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        # Check whether the developer belongs to this group.
        is_member = await self.check_group_membership()

        if not is_member:
            await self.close(code=4403)
            return

        # Add this connection to the group's broadcast channel.
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        # Accept the WebSocket connection.
        await self.accept()

    async def disconnect(self, close_code):
        """Remove the developer from the group's channel."""

        # Only remove connections that successfully joined a group.
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def chat_message(self, event):
        """Send a message event to the developer's browser."""

        await self.send_json(event["data"])

    @database_sync_to_async
    def check_group_membership(self):
        """Check group membership using Django's database."""

        # Find the group.
        group = ProjectGroup.objects.filter(
            id=self.group_id
        ).first()

        # Reject connections to groups that do not exist.
        if group is None:
            return False

        # IMPORTANT:
        # Replace this with the same membership check used
        # by your existing group chat Django views.
        from .views import is_group_member

        return is_group_member(group, self.user)



class GroupDiscussionConsumer(AsyncJsonWebsocketConsumer):
    """Send real-time discussion updates to group members."""

    async def connect(self):
        """Connect a developer to discussion updates."""

        # Get the logged-in developer.
        self.user = self.scope["user"]

        # Get the group ID from the WebSocket URL.
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]

        # Create a separate channel group for discussions.
        self.room_group_name = f"group_discussions_{self.group_id}"

        # Reject developers who are not logged in.
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        # Check whether the developer belongs to the group.
        is_member = await self.check_group_membership()

        if not is_member:
            await self.close(code=4403)
            return

        # Join the discussion broadcast group.
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        # Accept the WebSocket connection.
        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from discussion updates."""

        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def discussion_like(self, event):
        """Send the updated discussion like count."""

        await self.send_json(event["data"])

        # Receive a new comment event and send it to the browser.
    async def discussion_comment(self, event):
        """Send new comments to connected group members."""

        await self.send_json(event["data"])

    @database_sync_to_async
    def check_group_membership(self):
        """Check whether the developer belongs to the group."""

        from .models import GroupMember

        return GroupMember.objects.filter(
            group_id=self.group_id,
            user=self.user,
        ).exists()