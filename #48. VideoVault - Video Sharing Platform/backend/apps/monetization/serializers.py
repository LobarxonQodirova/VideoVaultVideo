"""
Serializers for the monetization app.
"""
from rest_framework import serializers
from .models import AdCampaign, Revenue, Subscription, Donation


class AdCampaignSerializer(serializers.ModelSerializer):
    ctr = serializers.ReadOnlyField()

    class Meta:
        model = AdCampaign
        fields = [
            "id", "advertiser", "name", "campaign_type", "status",
            "video_url", "banner_image", "click_through_url", "ad_text",
            "target_countries", "total_budget", "daily_budget",
            "cost_per_view", "spent",
            "impressions", "clicks", "skip_count", "ctr",
            "start_date", "end_date", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "spent", "impressions", "clicks",
            "skip_count", "created_at", "updated_at",
        ]


class RevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revenue
        fields = [
            "id", "user", "source", "amount", "currency",
            "description", "video", "is_paid_out", "paid_out_at",
            "period_start", "period_end", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RevenueSummarySerializer(serializers.Serializer):
    total_earnings = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_pending = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=14, decimal_places=2)
    ad_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    subscription_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    donation_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            "id", "subscriber", "channel", "tier", "status",
            "price", "currency", "started_at",
            "current_period_end", "cancelled_at", "created_at",
        ]
        read_only_fields = [
            "id", "started_at", "cancelled_at", "created_at",
        ]


class DonationSerializer(serializers.ModelSerializer):
    donor_username = serializers.CharField(source="donor.username", read_only=True)
    recipient_username = serializers.CharField(source="recipient.username", read_only=True)

    class Meta:
        model = Donation
        fields = [
            "id", "donor", "donor_username",
            "recipient", "recipient_username",
            "amount", "currency", "message",
            "video", "stream", "external_payment_id", "created_at",
        ]
        read_only_fields = ["id", "external_payment_id", "created_at"]
