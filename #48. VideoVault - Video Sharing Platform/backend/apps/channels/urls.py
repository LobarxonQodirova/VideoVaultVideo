"""
URL patterns for the channels app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "channels"

router = DefaultRouter()
router.register(r"", views.ChannelViewSet, basename="channel")

urlpatterns = [
    path("subscriptions/", views.MySubscriptionsView.as_view(), name="my-subscriptions"),
    path(
        "<slug:channel_slug>/playlists/",
        views.ChannelPlaylistViewSet.as_view({"get": "list", "post": "create"}),
        name="channel-playlists",
    ),
    path(
        "<slug:channel_slug>/playlists/<uuid:pk>/",
        views.ChannelPlaylistViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="channel-playlist-detail",
    ),
    path("", include(router.urls)),
]
