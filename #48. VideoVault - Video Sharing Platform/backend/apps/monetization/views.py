"""
Views for the monetization app.
"""
from django.db.models import Sum, Q
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsCreator, IsAdmin
from .models import AdCampaign, Revenue, Subscription, Donation
from .serializers import (
    AdCampaignSerializer,
    RevenueSerializer,
    RevenueSummarySerializer,
    SubscriptionSerializer,
    DonationSerializer,
)


class AdCampaignViewSet(viewsets.ModelViewSet):
    serializer_class = AdCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "campaign_type"]
    search_fields = ["name"]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return AdCampaign.objects.all()
        return AdCampaign.objects.filter(advertiser=user)

    def perform_create(self, serializer):
        serializer.save(advertiser=self.request.user)


class RevenueViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of a creator's revenue records."""
    serializer_class = RevenueSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreator]
    filterset_fields = ["source", "is_paid_out"]
    ordering_fields = ["period_start", "amount"]

    def get_queryset(self):
        return Revenue.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        qs = self.get_queryset()
        total = qs.aggregate(total=Sum("amount"))["total"] or 0
        paid = qs.filter(is_paid_out=True).aggregate(total=Sum("amount"))["total"] or 0
        pending = total - paid
        ad = qs.filter(source=Revenue.Source.AD).aggregate(total=Sum("amount"))["total"] or 0
        sub = qs.filter(source=Revenue.Source.SUBSCRIPTION).aggregate(total=Sum("amount"))["total"] or 0
        don = qs.filter(
            source__in=[Revenue.Source.DONATION, Revenue.Source.SUPER_CHAT]
        ).aggregate(total=Sum("amount"))["total"] or 0
        data = {
            "total_earnings": total,
            "total_pending": pending,
            "total_paid": paid,
            "ad_revenue": ad,
            "subscription_revenue": sub,
            "donation_revenue": don,
        }
        serializer = RevenueSummarySerializer(data)
        return Response(serializer.data)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Subscription.objects.filter(
            Q(subscriber=user) | Q(channel__owner=user)
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        sub = self.get_object()
        if sub.subscriber != request.user:
            return Response(
                {"detail": "Only the subscriber can cancel."},
                status=status.HTTP_403_FORBIDDEN,
            )
        from django.utils import timezone
        sub.status = Subscription.Status.CANCELLED
        sub.cancelled_at = timezone.now()
        sub.save(update_fields=["status", "cancelled_at"])
        return Response(SubscriptionSerializer(sub).data)


class DonationViewSet(viewsets.ModelViewSet):
    serializer_class = DonationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        return Donation.objects.filter(
            Q(donor=user) | Q(recipient=user)
        ).select_related("donor", "recipient")

    def perform_create(self, serializer):
        serializer.save(donor=self.request.user)
