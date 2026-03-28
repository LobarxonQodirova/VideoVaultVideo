"""
Serializers for the notifications app.
"""
from rest_framework import serializers
from apps.accounts.serializers import UserPublicSerializer
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserPublicSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id", "recipient", "actor", "notification_type",
            "title", "message", "link",
            "target_video", "target_channel", "target_comment",
            "is_read", "read_at", "created_at",
        ]
        read_only_fields = [
            "id", "recipient", "actor", "notification_type",
            "title", "message", "link",
            "target_video", "target_channel", "target_comment",
            "created_at",
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "id", "email_new_video", "email_comments", "email_replies",
            "email_likes", "email_subscribers", "email_stream_live",
            "push_enabled", "push_new_video", "push_comments",
            "push_stream_live", "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]


class UnreadCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()
