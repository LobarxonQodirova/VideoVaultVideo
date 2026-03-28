"""
Celery tasks for periodic analytics computation.
"""
from celery import shared_task
from .services import AnalyticsAggregator


@shared_task
def compute_daily_video_analytics():
    """Run daily video analytics aggregation (yesterday)."""
    return AnalyticsAggregator.compute_video_analytics()


@shared_task
def compute_daily_channel_analytics():
    """Run daily channel analytics aggregation (yesterday)."""
    return AnalyticsAggregator.compute_channel_analytics()
