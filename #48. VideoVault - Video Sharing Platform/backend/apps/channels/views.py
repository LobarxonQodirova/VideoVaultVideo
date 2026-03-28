"""
Views for the channels app.
"""
from django.db.models import F
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsCreator, IsOwnerOrReadOnly
from .models import Channel, ChannelSubscription, ChannelPlaylist
from .serializers import (
    ChannelListSerializer,
    ChannelDetailSerializer,
    ChannelCreateSerializer,
    ChannelSubscriptionSerializer,
    ChannelPlaylistSerializer,
)


class ChannelViewSet(viewsets.ModelViewSet):
    """CRUD + subscription management for channels."""
    lookup_field = "slug"
    filterset_fields = ["is_verified", "country"]
    search_fields = ["name", "description"]
    ordering_fields = ["subscriber_count", "video_count", "created_at"]

    def get_queryset(self):
        return Channel.objects.select_related("owner")

    def get_serializer_class(self):
        if self.action == "create":
            return ChannelCreateSerializer
        if self.action == "list":
            return ChannelListSerializer
        return ChannelDetailSerializer

    def get_permissions(self):
        if self.action in ("create",):
            return [permissions.IsAuthenticated(), IsCreator()]
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # ---- Subscribe / Unsubscribe ----
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, slug=None):
        channel = self.get_object()
        if channel.owner == request.user:
            return Response(
                {"detail": "You cannot subscribe to your own channel."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sub, created = ChannelSubscription.objects.get_or_create(
            channel=channel, user=request.user
        )
        if not created:
            return Response({"detail": "Already subscribed."})
        Channel.objects.filter(pk=channel.pk).update(subscriber_count=F("subscriber_count") + 1)
        return Response({"detail": "Subscribed."}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def unsubscribe(self, request, slug=None):
        channel = self.get_object()
        deleted, _ = ChannelSubscription.objects.filter(
            channel=channel, user=request.user
        ).delete()
        if deleted:
            Channel.objects.filter(pk=channel.pk).update(
                subscriber_count=F("subscriber_count") - 1
            )
            return Response({"detail": "Unsubscribed."})
        return Response({"detail": "Not subscribed."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def videos(self, request, slug=None):
        """List published videos for a channel."""
        from apps.videos.serializers import VideoListSerializer
        from apps.videos.models import Video

        channel = self.get_object()
        qs = Video.objects.filter(
            channel=channel,
            status=Video.Status.PUBLISHED,
        ).select_related("uploader", "category")
        page = self.paginate_queryset(qs)
        serializer = VideoListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class MySubscriptionsView(generics.ListAPIView):
    """List channels the authenticated user is subscribed to."""
    serializer_class = ChannelSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChannelSubscription.objects.filter(
            user=self.request.user
        ).select_related("channel__owner")


class ChannelPlaylistViewSet(viewsets.ModelViewSet):
    """CRUD for playlists owned by a channel."""
    serializer_class = ChannelPlaylistSerializer

    def get_queryset(self):
        return ChannelPlaylist.objects.filter(channel__slug=self.kwargs["channel_slug"])

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        channel = Channel.objects.get(slug=self.kwargs["channel_slug"])
        serializer.save(channel=channel)
