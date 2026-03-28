"""
URL patterns for the videos app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "videos"

router = DefaultRouter()
router.register(r"", views.VideoViewSet, basename="video")

urlpatterns = [
    path("categories/", views.VideoCategoryListView.as_view(), name="category-list"),
    path("tags/", views.VideoTagListView.as_view(), name="tag-list"),
    path(
        "<slug:video_slug>/comments/",
        views.VideoCommentViewSet.as_view({"get": "list", "post": "create"}),
        name="video-comments",
    ),
    path(
        "<slug:video_slug>/comments/<uuid:pk>/",
        views.VideoCommentViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="video-comment-detail",
    ),
    path("", include(router.urls)),
]
