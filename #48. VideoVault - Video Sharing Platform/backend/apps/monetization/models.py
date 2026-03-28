"""
Models for the monetization app.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AdCampaign(models.Model):
    """An advertising campaign that can be attached to videos."""

    class CampaignType(models.TextChoices):
        PRE_ROLL = "pre_roll", _("Pre-roll")
        MID_ROLL = "mid_roll", _("Mid-roll")
        POST_ROLL = "post_roll", _("Post-roll")
        BANNER = "banner", _("Banner overlay")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        ACTIVE = "active", _("Active")
        PAUSED = "paused", _("Paused")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    advertiser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ad_campaigns",
    )
    name = models.CharField(max_length=200)
    campaign_type = models.CharField(
        max_length=20, choices=CampaignType.choices, default=CampaignType.PRE_ROLL
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )

    # Creative assets
    video_url = models.URLField(blank=True, help_text="URL of the ad video")
    banner_image = models.ImageField(upload_to="ads/banners/", blank=True, null=True)
    click_through_url = models.URLField(blank=True)
    ad_text = models.CharField(max_length=300, blank=True)

    # Targeting
    target_categories = models.ManyToManyField(
        "videos.VideoCategory", blank=True, related_name="targeting_campaigns"
    )
    target_countries = models.JSONField(
        default=list, blank=True, help_text='List of ISO 3166-1 alpha-2 codes'
    )

    # Budget
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    daily_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_view = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Metrics
    impressions = models.PositiveBigIntegerField(default=0)
    clicks = models.PositiveBigIntegerField(default=0)
    skip_count = models.PositiveBigIntegerField(default=0)

    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ad_campaigns"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def ctr(self):
        """Click-through rate."""
        if self.impressions == 0:
            return 0
        return round(self.clicks / self.impressions * 100, 2)


class Revenue(models.Model):
    """Revenue record for a creator from ads, subscriptions, or donations."""

    class Source(models.TextChoices):
        AD = "ad", _("Ad revenue")
        SUBSCRIPTION = "subscription", _("Subscription")
        DONATION = "donation", _("Donation")
        SUPER_CHAT = "super_chat", _("Super chat")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="revenue_records",
    )
    source = models.CharField(max_length=20, choices=Source.choices, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    description = models.TextField(blank=True)
    video = models.ForeignKey(
        "videos.Video",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revenue_records",
    )
    is_paid_out = models.BooleanField(default=False)
    paid_out_at = models.DateTimeField(null=True, blank=True)
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "revenue"
        ordering = ["-period_start"]

    def __str__(self):
        return f"{self.user.username} | {self.source} | {self.amount} {self.currency}"


class Subscription(models.Model):
    """Premium channel subscription (paid tier)."""

    class Tier(models.TextChoices):
        BASIC = "basic", _("Basic")
        STANDARD = "standard", _("Standard")
        PREMIUM = "premium", _("Premium")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        CANCELLED = "cancelled", _("Cancelled")
        EXPIRED = "expired", _("Expired")
        PAST_DUE = "past_due", _("Past due")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paid_subscriptions",
    )
    channel = models.ForeignKey(
        "channels.Channel",
        on_delete=models.CASCADE,
        related_name="paid_subscriptions",
    )
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.BASIC)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")

    # Payment provider reference
    external_subscription_id = models.CharField(max_length=200, blank=True)
    external_customer_id = models.CharField(max_length=200, blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subscriptions"
        unique_together = ["subscriber", "channel"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subscriber.username} -> {self.channel.name} ({self.tier})"


class Donation(models.Model):
    """One-time donation / tip from a viewer to a creator."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donations_sent",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donations_received",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    message = models.TextField(blank=True, max_length=500)
    video = models.ForeignKey(
        "videos.Video",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations",
    )
    stream = models.ForeignKey(
        "streaming.LiveStream",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations",
    )
    external_payment_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "donations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.donor.username} -> {self.recipient.username}: {self.amount} {self.currency}"
