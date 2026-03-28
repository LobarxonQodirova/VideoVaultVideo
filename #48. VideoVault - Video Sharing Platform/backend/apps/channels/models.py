"""
Models for the channels app.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Channel(models.Model):
    """
    A channel owned by a creator.  Every creator gets at least one channel.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_channels",
    )
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True, max_length=2000)
    avatar = models.ImageField(upload_to="channels/avatars/%Y/%m/", blank=True, null=True)
    banner = models.ImageField(upload_to="channels/banners/%Y/%m/", blank=True, null=True)
    trailer_video = models.ForeignKey(
        "videos.Video",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    # Counters (denormalised)
    subscriber_count = models.PositiveBigIntegerField(default=0)
    video_count = models.PositiveIntegerField(default=0)
    total_views = models.PositiveBigIntegerField(default=0)

    # Links
    website = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    is_verified = models.BooleanField(default=False)
    country = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "channels"
        ordering = ["-subscriber_count"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or f"channel-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ChannelSubscription(models.Model):
    """Tracks a user subscribing to a channel."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="subscriptions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "channel_subscriptions"
        unique_together = ["channel", "user"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} -> {self.channel.name}"


class ChannelPlaylist(models.Model):
    """A playlist that belongs to a channel (channel-curated)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="channel_playlists"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True, max_length=1000)
    thumbnail = models.ImageField(upload_to="playlists/thumbnails/", blank=True, null=True)
    is_public = models.BooleanField(default=True)
    video_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "channel_playlists"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "playlist"
            self.slug = f"{base}-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.channel.name} – {self.title}"
