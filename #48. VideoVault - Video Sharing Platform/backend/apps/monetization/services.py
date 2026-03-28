"""
Business-logic services for monetization.
Handles revenue calculation, payout preparation, and ad-serving logic.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


class RevenueService:
    """Calculate and record creator revenue."""

    # Platform take-rate (30 % to platform, 70 % to creator)
    CREATOR_SHARE = Decimal("0.70")
    CPM_RATE = Decimal("2.50")  # default $ per 1 000 ad impressions

    @classmethod
    def calculate_ad_revenue_for_video(cls, video) -> Decimal:
        """
        Calculate ad revenue for a single video over the current period.
        Based on view count and CPM.
        """
        from apps.videos.models import VideoView

        period_start = timezone.now() - timedelta(days=30)
        views = VideoView.objects.filter(
            video=video,
            created_at__gte=period_start,
        ).count()

        gross = (Decimal(views) / Decimal(1000)) * cls.CPM_RATE
        creator_amount = (gross * cls.CREATOR_SHARE).quantize(Decimal("0.01"))
        return creator_amount

    @classmethod
    def record_period_revenue(cls, user, amount, source, period_start, period_end, video=None):
        """Create a Revenue record."""
        from .models import Revenue

        return Revenue.objects.create(
            user=user,
            source=source,
            amount=amount,
            period_start=period_start,
            period_end=period_end,
            video=video,
        )

    @classmethod
    def get_unpaid_total(cls, user) -> Decimal:
        from .models import Revenue
        total = Revenue.objects.filter(
            user=user, is_paid_out=False,
        ).aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0.00")

    @classmethod
    def mark_paid(cls, user, payment_reference: str = ""):
        """Mark all unpaid revenue as paid out."""
        from .models import Revenue

        now = timezone.now()
        updated = Revenue.objects.filter(
            user=user, is_paid_out=False,
        ).update(is_paid_out=True, paid_out_at=now)
        logger.info(
            "Marked %d revenue records as paid for user %s (ref: %s)",
            updated, user.username, payment_reference,
        )
        return updated


class AdService:
    """Select and serve ads for a given video view."""

    @staticmethod
    def select_ad_for_video(video, viewer_country: str = ""):
        """
        Return the best matching active AdCampaign for a video, or None.
        Matches on category and geo targeting, then picks the highest CPV.
        """
        from .models import AdCampaign

        today = date.today()
        qs = AdCampaign.objects.filter(
            status=AdCampaign.Status.ACTIVE,
            start_date__lte=today,
            end_date__gte=today,
        ).exclude(
            spent__gte=models.F("total_budget"),
        )

        if video.category:
            qs = qs.filter(
                models.Q(target_categories__isnull=True)
                | models.Q(target_categories=video.category)
            )

        if viewer_country:
            qs = qs.filter(
                models.Q(target_countries=[])
                | models.Q(target_countries__contains=[viewer_country])
            )

        return qs.order_by("-cost_per_view").first()

    @staticmethod
    def record_impression(campaign):
        """Increment impression count and spend."""
        from .models import AdCampaign
        from django.db.models import F

        AdCampaign.objects.filter(pk=campaign.pk).update(
            impressions=F("impressions") + 1,
            spent=F("spent") + F("cost_per_view"),
        )

    @staticmethod
    def record_click(campaign):
        from .models import AdCampaign
        from django.db.models import F

        AdCampaign.objects.filter(pk=campaign.pk).update(
            clicks=F("clicks") + 1,
        )
