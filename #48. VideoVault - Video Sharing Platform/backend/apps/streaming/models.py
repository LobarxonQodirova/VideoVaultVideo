"""
Models for the streaming (live) app.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class LiveStream(models.Model):
    """A live stream broadcast by a channel owner."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", _("Scheduled")
        LIVE = "live", _("Live")
        ENDED = "ended", _("Ended")
        CANCELLED = "cancelled", _("Cancelled")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        "channels.Channel",
        on_delete=models.CASCADE,
        related_name="live_streams",
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosted_streams",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, max_length=2000)
    thumbnail = models.ImageField(upload_to="streams/thumbnails/", blank=True, null=True)

    # Stream key for RTMP ingest
    stream_key = models.CharField(max_length=64, unique=True, editable=False)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
    )
    viewer_count = models.PositiveIntegerField(default=0)
    peak_viewer_count = models.PositiveIntegerField(default=0)
    chat_enabled = models.BooleanField(default=True)
    is_age_restricted = models.BooleanField(default=False)

    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "live_streams"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.stream_key:
            self.stream_key = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"


class StreamChat(models.Model):
    """Individual chat message in a live stream."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(
        LiveStream, on_delete=models.CASCADE, related_name="chat_messages"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stream_messages",
    )
    message = models.TextField(max_length=500)
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    # Donations / super-chats
    donation_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    donation_currency = models.CharField(max_length=3, blank=True, default="USD")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stream_chats"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.message[:40]}"


class StreamSchedule(models.Model):
    """Recurring or one-off schedule for upcoming streams."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        "channels.Channel",
        on_delete=models.CASCADE,
        related_name="stream_schedules",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(
        default=60, help_text="Expected duration in minutes"
    )
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(
        max_length=200,
        blank=True,
        help_text="iCal RRULE string for recurring streams",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stream_schedules"
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"{self.title} @ {self.scheduled_at}"
