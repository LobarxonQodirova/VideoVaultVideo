"""
Custom User model with role-based access for VideoVault.
"""
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom manager for User model that uses email as the unique identifier."""

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email address is required"))
        if not username:
            raise ValueError(_("Username is required"))
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model.
    Roles: VIEWER (default), CREATOR, MODERATOR, ADMIN.
    """

    class Role(models.TextChoices):
        VIEWER = "viewer", _("Viewer")
        CREATOR = "creator", _("Creator")
        MODERATOR = "moderator", _("Moderator")
        ADMIN = "admin", _("Admin")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(_("username"), max_length=40, unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        db_index=True,
    )
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, null=True)
    banner = models.ImageField(upload_to="banners/%Y/%m/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    website = models.URLField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_email_confirmed = models.BooleanField(default=False)

    # Social links
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_creator(self):
        return self.role in (self.Role.CREATOR, self.Role.ADMIN)

    @property
    def is_moderator(self):
        return self.role in (self.Role.MODERATOR, self.Role.ADMIN)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def subscriber_count(self):
        return self.owned_channels.aggregate(
            total=models.Sum("subscriptions__id")
        ).get("total") or 0
