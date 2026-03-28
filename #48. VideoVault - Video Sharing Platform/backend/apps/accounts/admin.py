"""
Django admin configuration for the accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "username", "email", "role", "is_verified",
        "is_active", "is_staff", "created_at",
    ]
    list_filter = ["role", "is_verified", "is_active", "is_staff", "created_at"]
    search_fields = ["username", "email", "bio"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (
            _("Profile"),
            {
                "fields": (
                    "avatar", "banner", "bio", "website",
                    "date_of_birth", "twitter_url", "instagram_url",
                ),
            },
        ),
        (
            _("Roles & verification"),
            {"fields": ("role", "is_verified", "is_email_confirmed")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active", "is_staff", "is_superuser",
                    "groups", "user_permissions",
                ),
            },
        ),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email", "username", "password1", "password2",
                    "role", "is_staff", "is_active",
                ),
            },
        ),
    )
