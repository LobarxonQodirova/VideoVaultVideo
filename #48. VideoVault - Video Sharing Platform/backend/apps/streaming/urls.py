"""
URL patterns for the streaming app (HTTP endpoints).
WebSocket routing is in routing.py and wired through ASGI.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "streaming"

router = DefaultRouter()
router.register(r"streams", views.LiveStreamViewSet, basename="livestream")
router.register(r"schedules", views.StreamScheduleViewSet, basename="stream-schedule")

urlpatterns = [
    path("", include(router.urls)),
]
