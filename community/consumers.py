"""
CodeView — WebSocket Consumers.

Handles:
1. Real-time group chat.
2. Real-time group discussions.
3. Private developer terminal connections.
4. Terminal session registration with FastAPI.
5. Terminal session disconnection.
"""

# Django Channels WebSocket consumer.
from channels.generic.websocket import AsyncJsonWebsocketConsumer

# Run synchronous Django database operations safely.
from channels.db import database_sync_to_async

# CodeView group models.
from .models import ProjectGroup, GroupMember

# Client for communicating with the FastAPI Runner Service.
from server_runner.client import (
    TerminalRunnerClient,
    RunnerUnavailableError,
)

# Service for creating terminal sessions.
from server_runner.services import create_terminal_session

# Database model for terminal sessions.
from server_runner.models import DeveloperTerminalSession


# ============================================================
# 1. GROUP CHAT CONSUMER
# ============================================================

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

         # Save the successful runner registration in PostgreSQL.
        await self.mark_runner_registered()
    async def disconnect(self, close_code):
        """Remove the developer from the group's channel."""

        # Only remove connections that joined the channel.
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

        # Find the requested group.
        group = ProjectGroup.objects.filter(
            id=self.group_id
        ).first()

        # Reject groups that do not exist.
        if group is None:
            return False

        # Use CodeView's existing membership helper.
        from .views import is_group_member

        return is_group_member(group, self.user)


# ============================================================
# 2. GROUP DISCUSSION CONSUMER
# ============================================================

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

        # Remove the connection from the discussion group.
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def discussion_like(self, event):
        """Send the updated discussion like count."""

        await self.send_json(event["data"])

    async def discussion_comment(self, event):
        """Send new comments to connected group members."""

        await self.send_json(event["data"])

    @database_sync_to_async
    def check_group_membership(self):
        """Check whether the developer belongs to the group."""

        # Check approved membership.
        is_member = GroupMember.objects.filter(
            group_id=self.group_id,
            user=self.user,
        ).exists()

        # Allow approved members.
        if is_member:
            return True

        # Also allow the group owner.
        return ProjectGroup.objects.filter(
            id=self.group_id,
            owner_id=self.user.pk,
        ).exists()


# ============================================================
# 3. TERMINAL CONSUMER
# ============================================================

class TerminalConsumer(AsyncJsonWebsocketConsumer):
    """Handle private developer terminal WebSocket connections."""

    async def connect(self):
        """Authenticate the developer and register a terminal session."""

        # Get the logged-in developer.
        self.user = self.scope["user"]

        # Get the group ID from the WebSocket URL.
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]

        # Initially, no terminal session exists.
        self.terminal_session_id = None

        # Step 1: Reject developers who are not logged in.
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        # Step 2: Verify membership and create a database session.
        session_data = await self.create_session()

        # Reject unauthorized developers.
        if session_data is None:
            await self.close(code=4403)
            return

        # Step 3: Store the session ID.
        self.terminal_session_id = session_data["session_id"]

        try:
            # Step 4: Create a client for communicating with FastAPI.
            runner = TerminalRunnerClient()

            # Step 5: Register the session with FastAPI.
            runner_response = await runner.create_session(
                session_id=self.terminal_session_id,
                developer_id=self.user.pk,
                group_id=self.group_id,
            )

            # Step 6: Verify the response from FastAPI.
            if (
                runner_response.get("session_id")
                != self.terminal_session_id
                or runner_response.get("status") != "registered"
            ):
                # Mark the database session as disconnected.
                await self.mark_session_disconnected()

                # Reject unexpected responses.
                await self.close(code=1011)
                return

        except RunnerUnavailableError:
            # FastAPI could not register the session.
            await self.mark_session_disconnected()

            # Reject the WebSocket connection.
            await self.close(code=1013)
            return

        # Save FastAPI's successful registration in PostgreSQL.
        await self.mark_runner_registered()

        # Step 7: Accept the WebSocket connection.
        await self.accept()

        # Step 8: Send session information to JavaScript.
        await self.send_json({
            "type": "terminal_connected",
            "message": "CodeView terminal session registered.",
            "session_id": self.terminal_session_id,
            "status": runner_response["status"],
        })

    @database_sync_to_async
    def create_session(self):
        """Verify private-group access and create a database session."""

        # Find the requested private development group.
        group = ProjectGroup.objects.filter(
            id=self.group_id,
            is_private=True,
        ).first()

        # Reject nonexistent or public groups.
        if group is None:
            return None

        try:
            # Create the terminal session for this developer.
            session = create_terminal_session(
                user=self.user,
                group=group,
            )

        except PermissionError:
            # Reject developers without permission.
            return None

        # Return the session information.
        return {
            "session_id": str(session.session_id),
            "status": session.status,
        }

    async def receive_json(self, content, **kwargs):
        """Receive terminal messages without executing commands."""

        # The sandbox execution backend is not connected yet.
        await self.send_json({
            "type": "terminal_info",
            "message": (
                "Terminal session registered. "
                "Sandbox execution is not connected yet."
            ),
        })

    async def disconnect(self, close_code):
        """Handle terminal WebSocket disconnection."""

        # No session means there is nothing to disconnect.
        if self.terminal_session_id is None:
            return

        try:
            # Notify the FastAPI Runner Service.
            runner = TerminalRunnerClient()

            await runner.disconnect_session(
                session_id=self.terminal_session_id,
            )

        except RunnerUnavailableError:
            # FastAPI may be temporarily unavailable.
            # We still need to update PostgreSQL.
            pass

        finally:
            # Always record the WebSocket disconnection.
            await self.mark_session_disconnected()

    @database_sync_to_async
    def mark_session_disconnected(self):
        """Mark the developer's terminal session as disconnected."""

        # Update only the session belonging to this developer.
        DeveloperTerminalSession.objects.filter(
            session_id=self.terminal_session_id,
            developer_id=self.user.pk,
            group_id=self.group_id,
        ).update(
            status="disconnected",
        )

    @database_sync_to_async
    def mark_runner_registered(self):
        """Record successful FastAPI registration in PostgreSQL."""

        # Import Django's timezone utilities.
        from django.utils import timezone

        # Update the session belonging to this developer.
        DeveloperTerminalSession.objects.filter(
            session_id=self.terminal_session_id,
            developer_id=self.user.pk,
            group_id=self.group_id,
        ).update(
            runner_status="registered",
            runner_registered_at=timezone.now(),
        )

    async def disconnect_session(self, session_id):
        """Notify FastAPI that a terminal session disconnected."""

        # Authentication header.
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        try:
            # Create an asynchronous HTTP client.
            async with httpx.AsyncClient(timeout=10.0) as client:

                # Notify FastAPI about the disconnection.
                response = await client.post(
                    f"{self.base_url}/internal/sessions/{session_id}/disconnect",
                    headers=headers,
                )

                # Detect unsuccessful HTTP responses.
                response.raise_for_status()

                # Return FastAPI's response.
                return response.json()

        except httpx.HTTPError as error:
            raise RunnerUnavailableError(
                "Failed to notify runner about disconnection."
            ) from error