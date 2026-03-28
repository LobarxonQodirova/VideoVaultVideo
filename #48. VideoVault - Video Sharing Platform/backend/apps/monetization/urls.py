"""
URL patterns for the monetization app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "monetization"

router = DefaultRouter()
router.register(r"campaigns", views.AdCampaignViewSet, basename="ad-campaign")
router.register(r"revenue", views.RevenueViewSet, basename="revenue")
router.register(r"subscriptions", views.SubscriptionViewSet, basename="subscription")
router.register(r"donations", views.DonationViewSet, basename="donation")

urlpatterns = [
    path("", include(router.urls)),
]
