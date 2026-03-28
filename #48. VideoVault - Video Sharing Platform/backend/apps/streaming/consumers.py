"""
WebSocket consumer for live-stream chat.
Uses Django Channels with Redis as the channel layer.
"""
import json
import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class StreamChatConsumer(AsyncJsonWebsocketConsumer):
    """
    Handles WebSocket connections for live-stream chat rooms.

    URL pattern: ws/stream/<stream_id>/chat/
    Group name:  stream_chat_<stream_id>
    """

    async def connect(self):
        self.stream_id = self.scope["url_route"]["kwargs"]["stream_id"]
        self.group_name = f"stream_chat_{self.stream_id}"
        self.user = self.scope.get("user")

        # Join the room group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Notify the room that a viewer joined
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "viewer_join",
                    "username": self.user.username,
                },
            )
            await self._update_viewer_count(1)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "viewer_leave",
                    "username": self.user.username,
                },
            )
            await self._update_viewer_count(-1)

    async def receive_json(self, content, **kwargs):
        """Handle incoming chat messages from the client."""
        msg_type = content.get("type", "chat_message")

        if msg_type == "chat_message":
            message = content.get("message", "").strip()
            if not message or not self.user or not self.user.is_authenticated:
                return

            # Persist the message
            chat_msg = await self._save_message(message)

            # Broadcast to the room
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat_message",
                    "id": str(chat_msg.id),
                    "username": self.user.username,
                    "avatar": await self._get_avatar_url(),
                    "message": message,
                    "timestamp": chat_msg.created_at.isoformat(),
                    "donation_amount": str(chat_msg.donation_amount) if chat_msg.donation_amount else None,
                },
            )

        elif msg_type == "pin_message":
            message_id = content.get("message_id")
            if await self._is_stream_host():
                await self._pin_message(message_id)
                await self.channel_layer.group_send(
                    self.group_name,
                    {"type": "message_pinned", "message_id": message_id},
                )

        elif msg_type == "delete_message":
            message_id = content.get("message_id")
            if await self._is_stream_host():
                await self._delete_message(message_id)
                await self.channel_layer.group_send(
                    self.group_name,
                    {"type": "message_deleted", "message_id": message_id},
                )

    # ---- Group event handlers ----

    async def chat_message(self, event):
        await self.send_json({
            "type": "chat_message",
            "id": event["id"],
            "username": event["username"],
            "avatar": event.get("avatar"),
            "message": event["message"],
            "timestamp": event["timestamp"],
            "donation_amount": event.get("donation_amount"),
        })

    async def viewer_join(self, event):
        await self.send_json({
            "type": "viewer_join",
            "username": event["username"],
        })

    async def viewer_leave(self, event):
        await self.send_json({
            "type": "viewer_leave",
            "username": event["username"],
        })

    async def message_pinned(self, event):
        await self.send_json({
            "type": "message_pinned",
            "message_id": event["message_id"],
        })

    async def message_deleted(self, event):
        await self.send_json({
            "type": "message_deleted",
            "message_id": event["message_id"],
        })

    # ---- Database helpers (sync -> async) ----

    @database_sync_to_async
    def _save_message(self, message):
        from .models import StreamChat, LiveStream
        stream = LiveStream.objects.get(pk=self.stream_id)
        return StreamChat.objects.create(
            stream=stream,
            user=self.user,
            message=message,
        )

    @database_sync_to_async
    def _update_viewer_count(self, delta):
        from .models import LiveStream
        from django.db.models import F
        LiveStream.objects.filter(pk=self.stream_id).update(
            viewer_count=F("viewer_count") + delta
        )
        stream = LiveStream.objects.get(pk=self.stream_id)
        if stream.viewer_count > stream.peak_viewer_count:
            stream.peak_viewer_count = stream.viewer_count
            stream.save(update_fields=["peak_viewer_count"])

    @database_sync_to_async
    def _is_stream_host(self):
        from .models import LiveStream
        try:
            stream = LiveStream.objects.select_related("host").get(pk=self.stream_id)
            return stream.host == self.user
        except LiveStream.DoesNotExist:
            return False

    @database_sync_to_async
    def _get_avatar_url(self):
        if self.user.avatar:
            return self.user.avatar.url
        return None

    @database_sync_to_async
    def _pin_message(self, message_id):
        from .models import StreamChat
        StreamChat.objects.filter(pk=message_id, stream_id=self.stream_id).update(is_pinned=True)

    @database_sync_to_async
    def _delete_message(self, message_id):
        from .models import StreamChat
        StreamChat.objects.filter(pk=message_id, stream_id=self.stream_id).update(is_deleted=True)
