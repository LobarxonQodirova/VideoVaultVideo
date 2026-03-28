"""
Views for the notifications app.
"""
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
    UnreadCountSerializer,
)


class NotificationListView(generics.ListAPIView):
    """List the authenticated user's notifications."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["notification_type", "is_read"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
        ).select_related("actor")


class NotificationMarkReadView(APIView):
    """Mark one or more notifications as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        notification_ids = request.data.get("notification_ids", [])
        now = timezone.now()

        if notification_ids:
            updated = Notification.objects.filter(
                id__in=notification_ids,
                recipient=request.user,
                is_read=False,
            ).update(is_read=True, read_at=now)
        else:
            # Mark all as read
            updated = Notification.objects.filter(
                recipient=request.user,
                is_read=False,
            ).update(is_read=True, read_at=now)

        return Response({"marked_read": updated})


class UnreadCountView(APIView):
    """Return the count of unread notifications."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return Response(UnreadCountSerializer({"unread_count": count}).data)


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated user's notification preferences."""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, _ = NotificationPreference.objects.get_or_create(
            user=self.request.user,
        )
        return obj
