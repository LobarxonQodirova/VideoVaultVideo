"""
Views for the analytics app.
Provides channel and video analytics dashboards for creators.
"""
from datetime import timedelta

from django.db.models import Sum, Avg
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsCreator
from .models import ChannelAnalytics, VideoAnalytics, AudienceDemographic, TrafficSource
from .serializers import (
    ChannelAnalyticsSerializer,
    VideoAnalyticsSerializer,
    AudienceDemographicSerializer,
    TrafficSourceSerializer,
    ChannelOverviewSerializer,
)


class ChannelOverviewView(APIView):
    """
    Return an aggregated analytics overview for a channel owned by the
    authenticated creator. Accepts ?days=N query parameter (default 30).
    """
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def get(self, request, channel_id):
        days = int(request.query_params.get("days", 30))
        start_date = timezone.now().date() - timedelta(days=days)

        qs = ChannelAnalytics.objects.filter(
            channel_id=channel_id,
            channel__owner=request.user,
            date__gte=start_date,
        )

        agg = qs.aggregate(
            total_views=Sum("views"),
            total_watch_time=Sum("watch_time_seconds"),
            total_subscribers_gained=Sum("new_subscribers"),
            total_subscribers_lost=Sum("lost_subscribers"),
            total_likes=Sum("likes"),
            total_comments=Sum("comments"),
            estimated_revenue=Sum("estimated_revenue"),
        )

        data = {
            "total_views": agg["total_views"] or 0,
            "total_watch_time": agg["total_watch_time"] or 0,
            "total_subscribers_gained": agg["total_subscribers_gained"] or 0,
            "total_subscribers_lost": agg["total_subscribers_lost"] or 0,
            "net_subscribers": (agg["total_subscribers_gained"] or 0) - (agg["total_subscribers_lost"] or 0),
            "total_likes": agg["total_likes"] or 0,
            "total_comments": agg["total_comments"] or 0,
            "estimated_revenue": agg["estimated_revenue"] or 0,
            "daily_breakdown": ChannelAnalyticsSerializer(qs, many=True).data,
        }
        return Response(ChannelOverviewSerializer(data).data)


class VideoAnalyticsListView(generics.ListAPIView):
    """List daily analytics for a specific video owned by the creator."""
    serializer_class = VideoAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def get_queryset(self):
        video_id = self.kwargs["video_id"]
        days = int(self.request.query_params.get("days", 30))
        start_date = timezone.now().date() - timedelta(days=days)
        return VideoAnalytics.objects.filter(
            video_id=video_id,
            video__uploader=self.request.user,
            date__gte=start_date,
        )


class AudienceDemographicsView(generics.ListAPIView):
    """List audience demographics for a channel."""
    serializer_class = AudienceDemographicSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def get_queryset(self):
        channel_id = self.kwargs["channel_id"]
        return AudienceDemographic.objects.filter(
            channel_id=channel_id,
            channel__owner=self.request.user,
        ).order_by("-date", "-viewer_percentage")[:100]


class TrafficSourceView(generics.ListAPIView):
    """List traffic sources for a video."""
    serializer_class = TrafficSourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def get_queryset(self):
        video_id = self.kwargs["video_id"]
        days = int(self.request.query_params.get("days", 30))
        start_date = timezone.now().date() - timedelta(days=days)
        return TrafficSource.objects.filter(
            video_id=video_id,
            video__uploader=self.request.user,
            date__gte=start_date,
        )


class TopVideosView(APIView):
    """Return the creator's top-performing videos over a period."""
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def get(self, request, channel_id):
        days = int(request.query_params.get("days", 30))
        start_date = timezone.now().date() - timedelta(days=days)
        limit = int(request.query_params.get("limit", 10))

        qs = (
            VideoAnalytics.objects.filter(
                video__channel_id=channel_id,
                video__channel__owner=request.user,
                date__gte=start_date,
            )
            .values("video", "video__title", "video__slug", "video__thumbnail")
            .annotate(
                total_views=Sum("views"),
                total_likes=Sum("likes"),
                avg_watch_pct=Avg("avg_watch_percentage"),
            )
            .order_by("-total_views")[:limit]
        )
        return Response(list(qs))
