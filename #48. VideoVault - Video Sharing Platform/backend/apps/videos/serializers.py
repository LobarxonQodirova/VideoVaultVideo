"""
Serializers for the videos app.
"""
from rest_framework import serializers
from apps.accounts.serializers import UserPublicSerializer
from .models import (
    Video, VideoCategory, VideoTag, VideoComment, VideoLike, Subtitle,
)


class VideoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoCategory
        fields = ["id", "name", "slug", "description", "icon", "order"]


class VideoTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoTag
        fields = ["id", "name", "slug"]


class SubtitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtitle
        fields = [
            "id", "language", "label", "file",
            "is_auto_generated", "is_default", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VideoListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for video listings / search results."""
    uploader = UserPublicSerializer(read_only=True)
    category = VideoCategorySerializer(read_only=True)
    formatted_duration = serializers.ReadOnlyField()
    channel_name = serializers.CharField(source="channel.name", read_only=True)

    class Meta:
        model = Video
        fields = [
            "id", "title", "slug", "thumbnail", "duration",
            "formatted_duration", "view_count", "like_count",
            "published_at", "uploader", "category", "channel_name",
            "is_age_restricted", "status",
        ]


class VideoDetailSerializer(serializers.ModelSerializer):
    """Full serializer for video detail view."""
    uploader = UserPublicSerializer(read_only=True)
    category = VideoCategorySerializer(read_only=True)
    tags = VideoTagSerializer(many=True, read_only=True)
    subtitles = SubtitleSerializer(many=True, read_only=True)
    formatted_duration = serializers.ReadOnlyField()
    is_public = serializers.ReadOnlyField()
    channel_name = serializers.CharField(source="channel.name", read_only=True)
    channel_id = serializers.UUIDField(source="channel.id", read_only=True)

    class Meta:
        model = Video
        fields = [
            "id", "title", "slug", "description",
            "original_file", "file_360p", "file_480p", "file_720p", "file_1080p",
            "thumbnail", "preview_gif",
            "duration", "formatted_duration", "file_size",
            "resolution_width", "resolution_height", "fps", "codec", "bitrate",
            "category", "tags", "subtitles",
            "status", "visibility", "processing_progress",
            "is_age_restricted", "allow_comments", "allow_embedding", "is_public",
            "view_count", "like_count", "dislike_count", "comment_count",
            "uploader", "channel_name", "channel_id",
            "published_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "slug", "view_count", "like_count", "dislike_count",
            "comment_count", "processing_progress", "status",
            "file_size", "duration", "resolution_width", "resolution_height",
            "fps", "codec", "bitrate", "published_at", "created_at", "updated_at",
        ]


class VideoUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading a new video."""
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=60),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Video
        fields = [
            "title", "description", "original_file", "thumbnail",
            "category", "tag_names", "visibility",
            "is_age_restricted", "allow_comments", "allow_embedding",
        ]

    def create(self, validated_data):
        tag_names = validated_data.pop("tag_names", [])
        video = Video.objects.create(**validated_data)
        for name in tag_names:
            tag, _ = VideoTag.objects.get_or_create(
                name=name,
                defaults={"slug": name.lower().replace(" ", "-")},
            )
            video.tags.add(tag)
        return video


class VideoCommentSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = VideoComment
        fields = [
            "id", "video", "user", "parent", "text",
            "like_count", "is_pinned", "is_hearted", "is_edited",
            "replies", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "user", "like_count", "is_pinned",
            "is_hearted", "is_edited", "created_at", "updated_at",
        ]

    def get_replies(self, obj):
        if obj.parent is not None:
            return []
        replies = obj.replies.select_related("user").order_by("created_at")[:10]
        return VideoCommentSerializer(replies, many=True).data


class VideoLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoLike
        fields = ["id", "video", "like_type", "created_at"]
        read_only_fields = ["id", "created_at"]
