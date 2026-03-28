"""
Django admin configuration for the channels app.
"""
from django.contrib import admin
from .models import Channel, ChannelSubscription, ChannelPlaylist


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = [
        "name", "owner", "subscriber_count",
        "video_count", "is_verified", "created_at",
    ]
    list_filter = ["is_verified", "country"]
    search_fields = ["name", "description", "owner__username"]
    readonly_fields = [
        "id", "slug", "subscriber_count", "video_count",
        "total_views", "created_at", "updated_at",
    ]
    raw_id_fields = ["owner", "trailer_video"]


@admin.register(ChannelSubscription)
class ChannelSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "channel", "notifications_enabled", "created_at"]
    list_filter = ["notifications_enabled"]
    raw_id_fields = ["user", "channel"]


@admin.register(ChannelPlaylist)
class ChannelPlaylistAdmin(admin.ModelAdmin):
    list_display = ["title", "channel", "video_count", "is_public", "created_at"]
    list_filter = ["is_public"]
    search_fields = ["title", "channel__name"]
    raw_id_fields = ["channel"]
