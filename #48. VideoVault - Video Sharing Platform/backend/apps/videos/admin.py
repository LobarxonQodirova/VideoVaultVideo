"""
Django admin configuration for the videos app.
"""
from django.contrib import admin
from .models import (
    Video, VideoCategory, VideoTag, VideoComment, VideoLike, VideoView, Subtitle,
)


@admin.register(VideoCategory)
class VideoCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["order", "name"]


@admin.register(VideoTag)
class VideoTagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


class SubtitleInline(admin.TabularInline):
    model = Subtitle
    extra = 0


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        "title", "uploader", "status", "visibility",
        "view_count", "like_count", "published_at",
    ]
    list_filter = ["status", "visibility", "category", "is_age_restricted"]
    search_fields = ["title", "description", "uploader__username"]
    readonly_fields = [
        "id", "slug", "view_count", "like_count", "dislike_count",
        "comment_count", "processing_progress", "created_at", "updated_at",
    ]
    inlines = [SubtitleInline]
    raw_id_fields = ["uploader", "channel"]
    date_hierarchy = "created_at"


@admin.register(VideoComment)
class VideoCommentAdmin(admin.ModelAdmin):
    list_display = ["user", "video", "text_preview", "is_pinned", "created_at"]
    list_filter = ["is_pinned", "is_hearted"]
    search_fields = ["text", "user__username"]
    raw_id_fields = ["user", "video", "parent"]

    @admin.display(description="Text")
    def text_preview(self, obj):
        return obj.text[:80]


@admin.register(VideoLike)
class VideoLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "video", "like_type", "created_at"]
    list_filter = ["like_type"]
    raw_id_fields = ["user", "video"]


@admin.register(VideoView)
class VideoViewAdmin(admin.ModelAdmin):
    list_display = ["video", "user", "watch_duration", "watch_percentage", "created_at"]
    list_filter = ["country"]
    raw_id_fields = ["user", "video"]
    date_hierarchy = "created_at"
