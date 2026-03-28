"""
URL patterns for the playlists app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "playlists"

router = DefaultRouter()
router.register(r"playlists", views.PlaylistViewSet, basename="playlist")
router.register(r"watch-later", views.WatchLaterViewSet, basename="watch-later")

urlpatterns = [
    path("", include(router.urls)),
]
