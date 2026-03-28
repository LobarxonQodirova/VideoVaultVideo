"""
Views for the streaming (live) app.
"""
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers as drf_serializers

from apps.accounts.permissions import IsCreator, IsOwnerOrReadOnly
from .models import LiveStream, StreamChat, StreamSchedule


# ---------------------------------------------------------------------------
# Serializers (co-located for the streaming module)
# ---------------------------------------------------------------------------

class LiveStreamSerializer(drf_serializers.ModelSerializer):
    host_username = drf_serializers.CharField(source="host.username", read_only=True)
    channel_name = drf_serializers.CharField(source="channel.name", read_only=True)

    class Meta:
        model = LiveStream
        fields = [
            "id", "channel", "host", "host_username", "channel_name",
            "title", "description", "thumbnail", "stream_key",
            "status", "viewer_count", "peak_viewer_count",
            "chat_enabled", "is_age_restricted",
            "scheduled_at", "started_at", "ended_at", "created_at",
        ]
        read_only_fields = [
            "id", "stream_key", "viewer_count", "peak_viewer_count",
            "started_at", "ended_at", "created_at",
        ]


class StreamChatSerializer(drf_serializers.ModelSerializer):
    username = drf_serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = StreamChat
        fields = [
            "id", "stream", "username", "message",
            "is_pinned", "donation_amount", "donation_currency",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class StreamScheduleSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = StreamSchedule
        fields = [
            "id", "channel", "title", "description",
            "scheduled_at", "duration_minutes",
            "is_recurring", "recurrence_rule", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class LiveStreamViewSet(viewsets.ModelViewSet):
    serializer_class = LiveStreamSerializer
    filterset_fields = ["status", "channel__slug"]
    search_fields = ["title"]
    ordering_fields = ["viewer_count", "started_at", "created_at"]

    def get_queryset(self):
        return LiveStream.objects.select_related("host", "channel")

    def get_permissions(self):
        if self.action in ("create",):
            return [permissions.IsAuthenticated(), IsCreator()]
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsCreator])
    def go_live(self, request, pk=None):
        stream = self.get_object()
        if stream.host != request.user:
            return Response({"detail": "Not the host."}, status=status.HTTP_403_FORBIDDEN)
        stream.status = LiveStream.Status.LIVE
        stream.started_at = timezone.now()
        stream.save(update_fields=["status", "started_at"])
        return Response(LiveStreamSerializer(stream).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsCreator])
    def end_stream(self, request, pk=None):
        stream = self.get_object()
        if stream.host != request.user:
            return Response({"detail": "Not the host."}, status=status.HTTP_403_FORBIDDEN)
        stream.status = LiveStream.Status.ENDED
        stream.ended_at = timezone.now()
        stream.save(update_fields=["status", "ended_at"])
        return Response(LiveStreamSerializer(stream).data)

    @action(detail=True, methods=["get"])
    def chat_history(self, request, pk=None):
        stream = self.get_object()
        messages = stream.chat_messages.filter(is_deleted=False).select_related("user")[:200]
        serializer = StreamChatSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Return all currently-live streams."""
        qs = self.get_queryset().filter(status=LiveStream.Status.LIVE)
        serializer = LiveStreamSerializer(qs, many=True)
        return Response(serializer.data)


class StreamScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = StreamScheduleSerializer
    filterset_fields = ["channel__slug", "is_recurring"]

    def get_queryset(self):
        return StreamSchedule.objects.filter(
            scheduled_at__gte=timezone.now()
        ).select_related("channel")

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsCreator()]
        return [permissions.AllowAny()]
