"""
Celery application configuration for VideoVault.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("videovault")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# ---------------------------------------------------------------------------
# Periodic tasks (Celery Beat)
# ---------------------------------------------------------------------------

app.conf.beat_schedule = {
    "aggregate-video-analytics-hourly": {
        "task": "apps.analytics.tasks.aggregate_video_analytics",
        "schedule": crontab(minute=0),  # every hour
    },
    "aggregate-channel-analytics-daily": {
        "task": "apps.analytics.tasks.aggregate_channel_analytics",
        "schedule": crontab(hour=2, minute=0),  # 02:00 UTC daily
    },
    "cleanup-stale-uploads-daily": {
        "task": "apps.videos.tasks.cleanup_stale_uploads",
        "schedule": crontab(hour=3, minute=30),  # 03:30 UTC daily
    },
    "send-digest-notifications-daily": {
        "task": "apps.notifications.tasks.send_daily_digest",
        "schedule": crontab(hour=8, minute=0),  # 08:00 UTC daily
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Simple task used to verify the Celery worker is running."""
    print(f"Request: {self.request!r}")
