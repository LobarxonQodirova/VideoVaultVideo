"""
Views for the playlists app.
"""
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsOwnerOrReadOnly
from apps.videos.models import Video
from .models import Playlist, PlaylistVideo, WatchLater
from .serializers import (
    PlaylistListSerializer,
    PlaylistDetailSerializer,
    PlaylistCreateSerializer,
    AddVideoToPlaylistSerializer,
    PlaylistVideoSerializer,
    WatchLaterSerializer,
)


class PlaylistViewSet(viewsets.ModelViewSet):
    """CRUD for user playlists."""
    lookup_field = "slug"
    filterset_fields = ["privacy"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "video_count"]

    def get_queryset(self):
        qs = Playlist.objects.select_related("user").prefetch_related(
            "playlist_videos__video"
        )
        if self.action == "list" and not self.request.user.is_authenticated:
            qs = qs.filter(privacy=Playlist.Privacy.PUBLIC)
        elif self.action == "list":
            from django.db.models import Q
            qs = qs.filter(
                Q(privacy=Playlist.Privacy.PUBLIC)
                | Q(user=self.request.user)
            )
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return PlaylistCreateSerializer
        if self.action == "list":
            return PlaylistListSerializer
        return PlaylistDetailSerializer

    def get_permissions(self):
        if self.action in ("create",):
            return [permissions.IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def add_video(self, request, slug=None):
        """Add a video to the playlist."""
        playlist = self.get_object()
        ser = AddVideoToPlaylistSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            video = Video.objects.get(pk=ser.validated_data["video_id"])
        except Video.DoesNotExist:
            return Response({"detail": "Video not found."}, status=status.HTTP_404_NOT_FOUND)

        position = ser.validated_data.get(
            "position",
            playlist.playlist_videos.count(),
        )
        pv, created = PlaylistVideo.objects.get_or_create(
            playlist=playlist, video=video,
            defaults={"position": position},
        )
        if not created:
            return Response({"detail": "Video already in playlist."}, status=status.HTTP_409_CONFLICT)
        playlist.recalculate()
        return Response(PlaylistVideoSerializer(pv).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def remove_video(self, request, slug=None):
        """Remove a video from the playlist."""
        playlist = self.get_object()
        video_id = request.data.get("video_id")
        deleted, _ = PlaylistVideo.objects.filter(
            playlist=playlist, video_id=video_id
        ).delete()
        if not deleted:
            return Response({"detail": "Video not in playlist."}, status=status.HTTP_404_NOT_FOUND)
        playlist.recalculate()
        return Response({"detail": "Removed."})


class WatchLaterViewSet(viewsets.ModelViewSet):
    """Manage the current user's Watch Later list."""
    serializer_class = WatchLaterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WatchLater.objects.filter(
            user=self.request.user
        ).select_related("video__uploader", "video__category")

    def create(self, request, *args, **kwargs):
        video_id = request.data.get("video_id")
        try:
            video = Video.objects.get(pk=video_id)
        except Video.DoesNotExist:
            return Response({"detail": "Video not found."}, status=status.HTTP_404_NOT_FOUND)

        wl, created = WatchLater.objects.get_or_create(user=request.user, video=video)
        if not created:
            return Response({"detail": "Already saved."}, status=status.HTTP_409_CONFLICT)
        return Response(WatchLaterSerializer(wl).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
