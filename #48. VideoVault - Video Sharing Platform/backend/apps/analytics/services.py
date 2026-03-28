"""
Services for the analytics app.
Handles computing and persisting daily analytics snapshots.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Avg, Q

logger = logging.getLogger(__name__)


class AnalyticsAggregator:
    """Compute and store daily analytics snapshots."""

    @classmethod
    def compute_video_analytics(cls, target_date: date = None):
        """
        Compute per-video analytics for a given date and persist
        them as VideoAnalytics records.
        """
        from apps.videos.models import Video, VideoView, VideoLike, VideoComment
        from .models import VideoAnalytics

        target_date = target_date or date.today() - timedelta(days=1)
        videos = Video.objects.filter(status=Video.Status.PUBLISHED)

        created = 0
        for video in videos.iterator():
            views_qs = VideoView.objects.filter(
                video=video,
                created_at__date=target_date,
            )
            view_count = views_qs.count()
            if view_count == 0:
                continue

            unique_viewers = views_qs.values("user").distinct().count()
            avg_watch = views_qs.aggregate(
                pct=Avg("watch_percentage"),
                dur=Avg("watch_duration"),
            )
            likes = VideoLike.objects.filter(
                video=video, like_type="like", created_at__date=target_date,
            ).count()
            dislikes = VideoLike.objects.filter(
                video=video, like_type="dislike", created_at__date=target_date,
            ).count()
            comments = VideoComment.objects.filter(
                video=video, created_at__date=target_date,
            ).count()

            VideoAnalytics.objects.update_or_create(
                video=video,
                date=target_date,
                defaults={
                    "views": view_count,
                    "unique_viewers": unique_viewers,
                    "avg_watch_percentage": avg_watch["pct"] or 0,
                    "avg_watch_duration": avg_watch["dur"] or 0,
                    "likes": likes,
                    "dislikes": dislikes,
                    "comments": comments,
                },
            )
            created += 1

        logger.info("Computed video analytics for %s: %d videos", target_date, created)
        return created

    @classmethod
    def compute_channel_analytics(cls, target_date: date = None):
        """
        Aggregate per-channel analytics from video analytics snapshots.
        """
        from apps.channels.models import Channel, ChannelSubscription
        from .models import ChannelAnalytics, VideoAnalytics

        target_date = target_date or date.today() - timedelta(days=1)
        channels = Channel.objects.all()

        created = 0
        for channel in channels.iterator():
            video_agg = VideoAnalytics.objects.filter(
                video__channel=channel,
                date=target_date,
            ).aggregate(
                views=Sum("views"),
                likes=Sum("likes"),
                dislikes=Sum("dislikes"),
                comments=Sum("comments"),
            )

            new_subs = ChannelSubscription.objects.filter(
                channel=channel, created_at__date=target_date,
            ).count()

            watch_time = VideoAnalytics.objects.filter(
                video__channel=channel,
                date=target_date,
            ).aggregate(
                total=Sum("avg_watch_duration"),
            )["total"] or 0

            ChannelAnalytics.objects.update_or_create(
                channel=channel,
                date=target_date,
                defaults={
                    "views": video_agg["views"] or 0,
                    "watch_time_seconds": int(watch_time),
                    "new_subscribers": new_subs,
                    "likes": video_agg["likes"] or 0,
                    "dislikes": video_agg["dislikes"] or 0,
                    "comments": video_agg["comments"] or 0,
                },
            )
            created += 1

        logger.info("Computed channel analytics for %s: %d channels", target_date, created)
        return created
