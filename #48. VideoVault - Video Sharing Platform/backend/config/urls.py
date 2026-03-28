"""
Root URL configuration for VideoVault.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/videos/", include("apps.videos.urls")),
    path("api/v1/channels/", include("apps.channels.urls")),
    path("api/v1/playlists/", include("apps.playlists.urls")),
    path("api/v1/streaming/", include("apps.streaming.urls")),
    path("api/v1/monetization/", include("apps.monetization.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),

    # OpenAPI schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
