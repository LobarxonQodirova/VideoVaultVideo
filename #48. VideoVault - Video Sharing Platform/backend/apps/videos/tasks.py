"""
Celery tasks for video processing: transcoding, thumbnail extraction, etc.
"""
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


def _run_ffprobe(file_path: str) -> dict:
    """Run ffprobe and return parsed JSON metadata."""
    cmd = [
        settings.FFMPEG_PATH.replace("ffmpeg", "ffprobe"),
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return json.loads(result.stdout)


def _transcode(input_path: str, output_path: str, height: int) -> bool:
    """Transcode video to a given resolution (height) using H.264."""
    cmd = [
        settings.FFMPEG_PATH,
        "-y",
        "-i", input_path,
        "-vf", f"scale=-2:{height}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]
    logger.info("Transcoding to %dp: %s", height, " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        logger.error("Transcode %dp failed: %s", height, result.stderr)
        return False
    return True


def _extract_thumbnail(input_path: str, output_path: str, position: float = 2.0) -> bool:
    """Extract a single frame as a JPEG thumbnail."""
    cmd = [
        settings.FFMPEG_PATH,
        "-y",
        "-ss", str(position),
        "-i", input_path,
        "-vframes", "1",
        "-q:v", "2",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.returncode == 0


def _generate_preview_gif(input_path: str, output_path: str, duration: float) -> bool:
    """Generate an animated GIF preview (5 seconds, low fps)."""
    start = max(0, duration * 0.1)
    cmd = [
        settings.FFMPEG_PATH,
        "-y",
        "-ss", str(start),
        "-t", "5",
        "-i", input_path,
        "-vf", "fps=8,scale=320:-1:flags=lanczos",
        "-loop", "0",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def process_video(self, video_id: str):
    """
    Main video processing pipeline:
    1. Extract metadata via ffprobe
    2. Generate thumbnail (if not provided)
    3. Transcode to configured resolutions
    4. Generate preview GIF
    5. Mark video as published
    """
    from .models import Video  # deferred import to avoid circular

    try:
        video = Video.objects.get(pk=video_id)
    except Video.DoesNotExist:
        logger.error("Video %s not found, aborting.", video_id)
        return

    input_path = video.original_file.path
    if not os.path.isfile(input_path):
        video.status = Video.Status.FAILED
        video.save(update_fields=["status"])
        logger.error("Original file not found for video %s", video_id)
        return

    try:
        # ---- 1. Extract metadata ----
        probe = _run_ffprobe(input_path)
        fmt = probe.get("format", {})
        video_stream = next(
            (s for s in probe.get("streams", []) if s.get("codec_type") == "video"), {}
        )
        video.duration = float(fmt.get("duration", 0))
        video.bitrate = int(fmt.get("bit_rate", 0)) // 1000
        video.resolution_width = int(video_stream.get("width", 0))
        video.resolution_height = int(video_stream.get("height", 0))
        video.fps = eval(video_stream.get("r_frame_rate", "0/1")) if video_stream.get("r_frame_rate") else 0
        video.codec = video_stream.get("codec_name", "")
        video.processing_progress = 10
        video.save(update_fields=[
            "duration", "bitrate", "resolution_width", "resolution_height",
            "fps", "codec", "processing_progress",
        ])

        # ---- 2. Thumbnail ----
        if not video.thumbnail:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                thumb_path = tmp.name
            if _extract_thumbnail(input_path, thumb_path, position=min(2, video.duration / 2)):
                with open(thumb_path, "rb") as f:
                    video.thumbnail.save(
                        f"thumb_{video.id}.jpg",
                        ContentFile(f.read()),
                        save=False,
                    )
            os.unlink(thumb_path)
        video.processing_progress = 20
        video.save(update_fields=["thumbnail", "processing_progress"])

        # ---- 3. Transcode ----
        source_height = video.resolution_height
        resolutions = settings.VIDEO_TRANSCODE_RESOLUTIONS
        field_map = {360: "file_360p", 480: "file_480p", 720: "file_720p", 1080: "file_1080p"}
        total = len([r for r in resolutions if r <= source_height])
        done = 0

        for res in resolutions:
            if res > source_height:
                continue
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                out_path = tmp.name
            if _transcode(input_path, out_path, res):
                field_name = field_map[res]
                with open(out_path, "rb") as f:
                    getattr(video, field_name).save(
                        f"{video.id}_{res}p.mp4",
                        ContentFile(f.read()),
                        save=False,
                    )
                done += 1
                progress = 20 + int(70 * done / max(total, 1))
                video.processing_progress = progress
                video.save(update_fields=[field_name, "processing_progress"])
            os.unlink(out_path)

        # ---- 4. Preview GIF ----
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
            gif_path = tmp.name
        if _generate_preview_gif(input_path, gif_path, video.duration):
            with open(gif_path, "rb") as f:
                video.preview_gif.save(
                    f"preview_{video.id}.gif",
                    ContentFile(f.read()),
                    save=False,
                )
        os.unlink(gif_path)

        # ---- 5. Finalise ----
        video.status = Video.Status.PUBLISHED
        video.processing_progress = 100
        video.published_at = timezone.now()
        video.save(update_fields=["status", "processing_progress", "published_at", "preview_gif"])
        logger.info("Video %s processed successfully.", video_id)

    except Exception as exc:
        logger.exception("Video processing failed for %s", video_id)
        video.status = Video.Status.FAILED
        video.save(update_fields=["status"])
        raise self.retry(exc=exc)


@shared_task
def cleanup_stale_uploads():
    """Remove videos stuck in UPLOADING/PROCESSING for more than 24 hours."""
    from .models import Video
    cutoff = timezone.now() - timezone.timedelta(hours=24)
    stale = Video.objects.filter(
        status__in=[Video.Status.UPLOADING, Video.Status.PROCESSING],
        created_at__lt=cutoff,
    )
    count = stale.count()
    stale.update(status=Video.Status.FAILED)
    logger.info("Marked %d stale uploads as FAILED.", count)
