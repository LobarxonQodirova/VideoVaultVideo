"""
Models for the playlists app.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Playlist(models.Model):
    """User-created playlist."""

    class Privacy(models.TextChoices):
        PUBLIC = "public", "Public"
        UNLISTED = "unlisted", "Unlisted"
        PRIVATE = "private", "Private"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="playlists",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True, max_length=1000)
    thumbnail = models.ImageField(upload_to="playlists/thumbnails/", blank=True, null=True)
    privacy = models.CharField(
        max_length=20,
        choices=Privacy.choices,
        default=Privacy.PUBLIC,
    )
    video_count = models.PositiveIntegerField(default=0)
    total_duration = models.FloatField(default=0, help_text="Total seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "playlists"
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "playlist"
            self.slug = f"{base}-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def recalculate(self):
        """Recalculate video_count and total_duration from playlist videos."""
        agg = self.playlist_videos.aggregate(
            count=models.Count("id"),
            dur=models.Sum("video__duration"),
        )
        self.video_count = agg["count"] or 0
        self.total_duration = agg["dur"] or 0
        self.save(update_fields=["video_count", "total_duration"])


class PlaylistVideo(models.Model):
    """Through model for videos in a playlist with ordering."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playlist = models.ForeignKey(
        Playlist, on_delete=models.CASCADE, related_name="playlist_videos"
    )
    video = models.ForeignKey(
        "videos.Video", on_delete=models.CASCADE, related_name="playlist_entries"
    )
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "playlist_videos"
        unique_together = ["playlist", "video"]
        ordering = ["position"]

    def __str__(self):
        return f"{self.playlist.title}[{self.position}]: {self.video.title}"


class WatchLater(models.Model):
    """Shortcut playlist – saved videos to watch later."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watch_later",
    )
    video = models.ForeignKey(
        "videos.Video", on_delete=models.CASCADE, related_name="watch_later_entries"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "watch_later"
        unique_together = ["user", "video"]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} – {self.video.title}"
