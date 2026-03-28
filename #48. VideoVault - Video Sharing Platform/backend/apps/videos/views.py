"""
Views for the videos app.
"""
from django.db.models import F
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from apps.accounts.permissions import IsCreator, IsOwnerOrReadOnly, IsOwnerOrModerator
from .models import (
    Video, VideoCategory, VideoTag, VideoComment, VideoLike, VideoView, Subtitle,
)
from .serializers import (
    VideoListSerializer, VideoDetailSerializer, VideoUploadSerializer,
    VideoCommentSerializer, VideoLikeSerializer,
    VideoCategorySerializer, VideoTagSerializer, SubtitleSerializer,
)
from .tasks import process_video


class VideoCategoryListView(generics.ListAPIView):
    queryset = VideoCategory.objects.all()
    serializer_class = VideoCategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class VideoTagListView(generics.ListAPIView):
    queryset = VideoTag.objects.all()
    serializer_class = VideoTagSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ["name"]


class VideoViewSet(viewsets.ModelViewSet):
    """CRUD for videos."""
    lookup_field = "slug"
    filterset_fields = ["category__slug", "status", "visibility", "uploader__username"]
    search_fields = ["title", "description"]
    ordering_fields = ["published_at", "view_count", "like_count", "created_at"]

    def get_queryset(self):
        qs = Video.objects.select_related("uploader", "category", "channel").prefetch_related("tags")
        if self.action == "list":
            qs = qs.filter(status=Video.Status.PUBLISHED, visibility=Video.Visibility.PUBLIC)
        return qs

    def get_serializer_class(self):
        if self.action in ("create",):
            return VideoUploadSerializer
        if self.action == "list":
            return VideoListSerializer
        return VideoDetailSerializer

    def get_permissions(self):
        if self.action in ("create",):
            return [permissions.IsAuthenticated(), IsCreator()]
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOwnerOrModerator()]
        return [permissions.AllowAny()]

    def get_parsers(self):
        if self.action == "create":
            return [MultiPartParser(), FormParser()]
        return super().get_parsers()

    def perform_create(self, serializer):
        # Automatically assign uploader and first owned channel
        user = self.request.user
        channel = user.owned_channels.first()
        video = serializer.save(
            uploader=user,
            channel=channel,
            status=Video.Status.PROCESSING,
            file_size=self.request.FILES["original_file"].size,
        )
        # Kick off async transcoding pipeline
        process_video.delay(str(video.id))

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def record_view(self, request, slug=None):
        """Record that a user watched part of this video."""
        video = self.get_object()
        VideoView.objects.create(
            video=video,
            user=request.user if request.user.is_authenticated else None,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            watch_duration=request.data.get("watch_duration", 0),
            watch_percentage=request.data.get("watch_percentage", 0),
        )
        Video.objects.filter(pk=video.pk).update(view_count=F("view_count") + 1)
        return Response({"detail": "View recorded."}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, slug=None):
        """Like or dislike a video (toggle)."""
        video = self.get_object()
        like_type = request.data.get("like_type", "like")
        if like_type not in ("like", "dislike"):
            return Response({"detail": "Invalid like_type."}, status=status.HTTP_400_BAD_REQUEST)

        existing = VideoLike.objects.filter(video=video, user=request.user).first()
        if existing:
            if existing.like_type == like_type:
                existing.delete()
                return Response({"detail": f"{like_type.capitalize()} removed."})
            existing.like_type = like_type
            existing.save(update_fields=["like_type"])
        else:
            VideoLike.objects.create(video=video, user=request.user, like_type=like_type)

        # Refresh counters
        video.like_count = video.likes.filter(like_type="like").count()
        video.dislike_count = video.likes.filter(like_type="dislike").count()
        video.save(update_fields=["like_count", "dislike_count"])
        return Response({"like_count": video.like_count, "dislike_count": video.dislike_count})

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def trending(self, request):
        """Return trending videos (most viewed in the last 7 days)."""
        week_ago = timezone.now() - timezone.timedelta(days=7)
        qs = (
            Video.objects.filter(
                status=Video.Status.PUBLISHED,
                visibility=Video.Visibility.PUBLIC,
                published_at__gte=week_ago,
            )
            .order_by("-view_count")[:40]
        )
        serializer = VideoListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser], permission_classes=[permissions.IsAuthenticated, IsCreator])
    def upload_subtitle(self, request, slug=None):
        video = self.get_object()
        serializer = SubtitleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(video=video)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VideoCommentViewSet(viewsets.ModelViewSet):
    """CRUD for comments on a specific video."""
    serializer_class = VideoCommentSerializer

    def get_queryset(self):
        return (
            VideoComment.objects
            .filter(video__slug=self.kwargs["video_slug"], parent__isnull=True)
            .select_related("user")
            .prefetch_related("replies__user")
        )

    def get_permissions(self):
        if self.action in ("create",):
            return [permissions.IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOwnerOrModerator()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        video = Video.objects.get(slug=self.kwargs["video_slug"])
        serializer.save(user=self.request.user, video=video)
        Video.objects.filter(pk=video.pk).update(comment_count=F("comment_count") + 1)
