"""
Serializers for the channels app.
"""
from rest_framework import serializers
from apps.accounts.serializers import UserPublicSerializer
from .models import Channel, ChannelSubscription, ChannelPlaylist


class ChannelListSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)

    class Meta:
        model = Channel
        fields = [
            "id", "name", "slug", "avatar",
            "subscriber_count", "video_count", "is_verified",
            "owner", "created_at",
        ]


class ChannelDetailSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = [
            "id", "name", "slug", "description",
            "avatar", "banner", "trailer_video",
            "subscriber_count", "video_count", "total_views",
            "website", "twitter_url", "instagram_url",
            "is_verified", "country",
            "owner", "is_subscribed",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "slug", "subscriber_count", "video_count", "total_views",
            "is_verified", "owner", "created_at", "updated_at",
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ChannelSubscription.objects.filter(
                channel=obj, user=request.user
            ).exists()
        return False


class ChannelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = [
            "name", "description", "avatar", "banner",
            "website", "twitter_url", "instagram_url", "country",
        ]


class ChannelSubscriptionSerializer(serializers.ModelSerializer):
    channel = ChannelListSerializer(read_only=True)

    class Meta:
        model = ChannelSubscription
        fields = ["id", "channel", "notifications_enabled", "created_at"]
        read_only_fields = ["id", "created_at"]


class ChannelPlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelPlaylist
        fields = [
            "id", "channel", "title", "slug", "description",
            "thumbnail", "is_public", "video_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "video_count", "created_at", "updated_at"]
