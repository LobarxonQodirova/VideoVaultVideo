"""
URL patterns for the notifications app.
"""
from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path("mark-read/", views.NotificationMarkReadView.as_view(), name="mark-read"),
    path("unread-count/", views.UnreadCountView.as_view(), name="unread-count"),
    path("preferences/", views.NotificationPreferenceView.as_view(), name="preferences"),
]
