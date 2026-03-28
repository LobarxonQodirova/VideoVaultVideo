"""
URL patterns for the analytics app.
"""
from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path(
        "channel/<uuid:channel_id>/overview/",
        views.ChannelOverviewView.as_view(),
        name="channel-overview",
    ),
    path(
        "channel/<uuid:channel_id>/demographics/",
        views.AudienceDemographicsView.as_view(),
        name="channel-demographics",
    ),
    path(
        "channel/<uuid:channel_id>/top-videos/",
        views.TopVideosView.as_view(),
        name="top-videos",
    ),
    path(
        "video/<uuid:video_id>/",
        views.VideoAnalyticsListView.as_view(),
        name="video-analytics",
    ),
    path(
        "video/<uuid:video_id>/traffic/",
        views.TrafficSourceView.as_view(),
        name="video-traffic",
    ),
]
