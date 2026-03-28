"""
Serializers for the playlists app.
"""
from rest_framework import serializers
from apps.accounts.serializers import UserPublicSerializer
from apps.videos.serializers import VideoListSerializer
from .models import Playlist, PlaylistVideo, WatchLater


class PlaylistVideoSerializer(serializers.ModelSerializer):
    video = VideoListSerializer(read_only=True)

    class Meta:
        model = PlaylistVideo
        fields = ["id", "video", "position", "added_at"]
        read_only_fields = ["id", "added_at"]


class PlaylistListSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    first_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = [
            "id", "title", "slug", "thumbnail", "first_thumbnail",
            "privacy", "video_count", "total_duration",
            "user", "created_at", "updated_at",
        ]

    def get_first_thumbnail(self, obj):
        if obj.thumbnail:
            return None
        first = obj.playlist_videos.select_related("video").first()
        if first and first.video.thumbnail:
            return first.video.thumbnail.url
        return None


class PlaylistDetailSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    videos = PlaylistVideoSerializer(source="playlist_videos", many=True, read_only=True)

    class Meta:
        model = Playlist
        fields = [
            "id", "title", "slug", "description", "thumbnail",
            "privacy", "video_count", "total_duration",
            "user", "videos", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "slug", "video_count", "total_duration",
            "created_at", "updated_at",
        ]


class PlaylistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = ["title", "description", "thumbnail", "privacy"]


class AddVideoToPlaylistSerializer(serializers.Serializer):
    video_id = serializers.UUIDField()
    position = serializers.IntegerField(required=False, min_value=0)


class WatchLaterSerializer(serializers.ModelSerializer):
    video = VideoListSerializer(read_only=True)

    class Meta:
        model = WatchLater
        fields = ["id", "video", "added_at"]
        read_only_fields = ["id", "added_at"]
