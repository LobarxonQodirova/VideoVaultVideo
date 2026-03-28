"""
Analytics models for tracking platform-wide and per-channel statistics.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ChannelAnalytics(models.Model):
    """Daily snapshot of channel-level metrics."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        "channels.Channel",
        on_delete=models.CASCADE,
        related_name="analytics_snapshots",
    )
    date = models.DateField(db_index=True)
    views = models.PositiveBigIntegerField(default=0)
    watch_time_seconds = models.PositiveBigIntegerField(default=0)
    new_subscribers = models.IntegerField(default=0)
    lost_subscribers = models.IntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    estimated_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "channel_analytics"
        unique_together = ["channel", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.channel.name} – {self.date}"


class VideoAnalytics(models.Model):
    """Daily snapshot of per-video metrics."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(
        "videos.Video",
        on_delete=models.CASCADE,
        related_name="analytics_snapshots",
    )
    date = models.DateField(db_index=True)
    views = models.PositiveBigIntegerField(default=0)
    unique_viewers = models.PositiveIntegerField(default=0)
    avg_watch_percentage = models.FloatField(default=0)
    avg_watch_duration = models.FloatField(default=0)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "video_analytics"
        unique_together = ["video", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.video.title} – {self.date}"


class AudienceDemographic(models.Model):
    """Aggregated audience demographics for a channel."""

    class AgeGroup(models.TextChoices):
        AGE_13_17 = "13-17", _("13-17")
        AGE_18_24 = "18-24", _("18-24")
        AGE_25_34 = "25-34", _("25-34")
        AGE_35_44 = "35-44", _("35-44")
        AGE_45_54 = "45-54", _("45-54")
        AGE_55_64 = "55-64", _("55-64")
        AGE_65_PLUS = "65+", _("65+")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        "channels.Channel",
        on_delete=models.CASCADE,
        related_name="demographics",
    )
    country = models.CharField(max_length=2)
    age_group = models.CharField(max_length=10, choices=AgeGroup.choices)
    viewer_percentage = models.FloatField(default=0, help_text="Percentage of total viewers")
    date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audience_demographics"
        ordering = ["-date", "-viewer_percentage"]

    def __str__(self):
        return f"{self.channel.name} | {self.country} | {self.age_group}"


class TrafficSource(models.Model):
    """Where viewers discover videos."""

    class SourceType(models.TextChoices):
        SEARCH = "search", _("Search")
        SUGGESTED = "suggested", _("Suggested videos")
        BROWSE = "browse", _("Browse features")
        CHANNEL_PAGE = "channel_page", _("Channel page")
        EXTERNAL = "external", _("External")
        DIRECT = "direct", _("Direct / URL")
        PLAYLIST = "playlist", _("Playlist")
        NOTIFICATION = "notification", _("Notification")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(
        "videos.Video",
        on_delete=models.CASCADE,
        related_name="traffic_sources",
    )
    source_type = models.CharField(max_length=20, choices=SourceType.choices, db_index=True)
    views = models.PositiveBigIntegerField(default=0)
    watch_time_seconds = models.PositiveBigIntegerField(default=0)
    date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "traffic_sources"
        unique_together = ["video", "source_type", "date"]
        ordering = ["-date", "-views"]

    def __str__(self):
        return f"{self.video.title} | {self.source_type} | {self.date}"
