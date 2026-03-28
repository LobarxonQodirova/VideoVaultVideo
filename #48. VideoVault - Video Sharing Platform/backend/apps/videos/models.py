"""
Models for the videos app.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class VideoCategory(models.Model):
    """Top-level categories (e.g. Music, Gaming, Education)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS icon class")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "video_categories"
        ordering = ["order", "name"]
        verbose_name_plural = "video categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class VideoTag(models.Model):
    """Tags that can be attached to videos."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        db_table = "video_tags"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Video(models.Model):
    """Core video model."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        UPLOADING = "uploading", _("Uploading")
        PROCESSING = "processing", _("Processing")
        PUBLISHED = "published", _("Published")
        UNLISTED = "unlisted", _("Unlisted")
        PRIVATE = "private", _("Private")
        FAILED = "failed", _("Failed")
        REMOVED = "removed", _("Removed")

    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        UNLISTED = "unlisted", _("Unlisted")
        PRIVATE = "private", _("Private")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        "channels.Channel",
        on_delete=models.CASCADE,
        related_name="videos",
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_videos",
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True, max_length=5000)

    # Files
    original_file = models.FileField(upload_to="videos/originals/%Y/%m/%d/")
    file_360p = models.FileField(upload_to="videos/360p/", blank=True, null=True)
    file_480p = models.FileField(upload_to="videos/480p/", blank=True, null=True)
    file_720p = models.FileField(upload_to="videos/720p/", blank=True, null=True)
    file_1080p = models.FileField(upload_to="videos/1080p/", blank=True, null=True)
    thumbnail = models.ImageField(upload_to="videos/thumbnails/%Y/%m/%d/", blank=True, null=True)
    preview_gif = models.FileField(upload_to="videos/previews/", blank=True, null=True)

    # Metadata
    duration = models.FloatField(default=0, help_text="Duration in seconds")
    file_size = models.BigIntegerField(default=0, help_text="Original file size in bytes")
    resolution_width = models.PositiveIntegerField(default=0)
    resolution_height = models.PositiveIntegerField(default=0)
    fps = models.FloatField(default=0)
    codec = models.CharField(max_length=50, blank=True)
    bitrate = models.PositiveIntegerField(default=0, help_text="Bitrate in kbps")

    # Relationships
    category = models.ForeignKey(
        VideoCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="videos",
    )
    tags = models.ManyToManyField(VideoTag, blank=True, related_name="videos")

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        db_index=True,
    )
    processing_progress = models.PositiveIntegerField(
        default=0, help_text="Transcoding progress 0-100"
    )
    is_age_restricted = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    allow_embedding = models.BooleanField(default=True)

    # Counters (denormalised for performance)
    view_count = models.PositiveBigIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    dislike_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    # Timestamps
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "videos"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["-published_at"]),
            models.Index(fields=["status", "visibility"]),
            models.Index(fields=["-view_count"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "video"
            self.slug = f"{base}-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_public(self):
        return self.status == self.Status.PUBLISHED and self.visibility == self.Visibility.PUBLIC

    @property
    def formatted_duration(self):
        m, s = divmod(int(self.duration), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class VideoComment(models.Model):
    """Comments on a video, supporting nested replies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    text = models.TextField(max_length=2000)
    like_count = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_hearted = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "video_comments"
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.text[:60]}"


class VideoLike(models.Model):
    """Like/dislike on a video."""

    class LikeType(models.TextChoices):
        LIKE = "like", _("Like")
        DISLIKE = "dislike", _("Dislike")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="video_likes"
    )
    like_type = models.CharField(max_length=10, choices=LikeType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "video_likes"
        unique_together = ["video", "user"]

    def __str__(self):
        return f"{self.user.username} {self.like_type}d {self.video.title}"


class VideoView(models.Model):
    """Track individual video views for analytics."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="video_views",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    watch_duration = models.FloatField(default=0, help_text="Seconds watched")
    watch_percentage = models.FloatField(default=0, help_text="0-100 percentage")
    country = models.CharField(max_length=2, blank=True)
    referrer = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "video_views"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["video", "-created_at"]),
        ]

    def __str__(self):
        name = self.user.username if self.user else "anonymous"
        return f"{name} viewed {self.video.title}"


class Subtitle(models.Model):
    """Subtitle/caption tracks for a video."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="subtitles")
    language = models.CharField(max_length=10, help_text="ISO 639-1 code, e.g. 'en'")
    label = models.CharField(max_length=100, help_text="Display label, e.g. 'English'")
    file = models.FileField(upload_to="videos/subtitles/")
    is_auto_generated = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "video_subtitles"
        unique_together = ["video", "language"]
        ordering = ["language"]

    def __str__(self):
        return f"{self.video.title} – {self.label}"
