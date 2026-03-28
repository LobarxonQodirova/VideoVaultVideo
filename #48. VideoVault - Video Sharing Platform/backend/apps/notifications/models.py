"""
Models for the notifications app.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """In-app notification sent to a user."""

    class NotificationType(models.TextChoices):
        NEW_VIDEO = "new_video", _("New video from subscription")
        COMMENT = "comment", _("Comment on your video")
        REPLY = "reply", _("Reply to your comment")
        LIKE = "like", _("Like on your video")
        SUBSCRIBER = "subscriber", _("New subscriber")
        MENTION = "mention", _("Mentioned in a comment")
        STREAM_LIVE = "stream_live", _("Subscribed channel went live")
        MILESTONE = "milestone", _("Channel milestone reached")
        SYSTEM = "system", _("System announcement")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        db_index=True,
    )
    title = models.CharField(max_length=200)
    message = models.TextField(max_length=500)
    link = models.URLField(blank=True, help_text="Deep link to the relevant content")

    # Generic relation fields to the target object
    target_video = models.ForeignKey(
        "videos.Video",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    target_channel = models.ForeignKey(
        "channels.Channel",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    target_comment = models.ForeignKey(
        "videos.VideoComment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title}"


class NotificationPreference(models.Model):
    """Per-user notification preferences."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    email_new_video = models.BooleanField(default=True)
    email_comments = models.BooleanField(default=True)
    email_replies = models.BooleanField(default=True)
    email_likes = models.BooleanField(default=False)
    email_subscribers = models.BooleanField(default=True)
    email_stream_live = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    push_new_video = models.BooleanField(default=True)
    push_comments = models.BooleanField(default=True)
    push_stream_live = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_preferences"

    def __str__(self):
        return f"Preferences for {self.user.username}"
