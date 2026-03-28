"""
Serializers for the analytics app.
"""
from rest_framework import serializers
from .models import ChannelAnalytics, VideoAnalytics, AudienceDemographic, TrafficSource


class ChannelAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelAnalytics
        fields = [
            "id", "channel", "date", "views", "watch_time_seconds",
            "new_subscribers", "lost_subscribers",
            "likes", "dislikes", "comments", "shares",
            "estimated_revenue", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VideoAnalyticsSerializer(serializers.ModelSerializer):
    video_title = serializers.CharField(source="video.title", read_only=True)

    class Meta:
        model = VideoAnalytics
        fields = [
            "id", "video", "video_title", "date",
            "views", "unique_viewers",
            "avg_watch_percentage", "avg_watch_duration",
            "likes", "dislikes", "comments", "shares",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AudienceDemographicSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudienceDemographic
        fields = [
            "id", "channel", "country", "age_group",
            "viewer_percentage", "date", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TrafficSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSource
        fields = [
            "id", "video", "source_type",
            "views", "watch_time_seconds", "date", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ChannelOverviewSerializer(serializers.Serializer):
    """Aggregated channel overview for the dashboard."""
    total_views = serializers.IntegerField()
    total_watch_time = serializers.IntegerField()
    total_subscribers_gained = serializers.IntegerField()
    total_subscribers_lost = serializers.IntegerField()
    net_subscribers = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    estimated_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    daily_breakdown = ChannelAnalyticsSerializer(many=True)
