"""
Custom DRF permissions for role-based access control.
"""
from rest_framework.permissions import BasePermission


class IsCreator(BasePermission):
    """Allow access only to users with the Creator or Admin role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_creator
        )


class IsModerator(BasePermission):
    """Allow access only to users with the Moderator or Admin role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_moderator
        )


class IsAdmin(BasePermission):
    """Allow access only to users with the Admin role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: allow write access only to the object's owner.
    The object must have a ``user`` or ``owner`` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user


class IsOwnerOrModerator(BasePermission):
    """
    Allow the object owner full access; moderators can also edit/delete.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        if owner == request.user:
            return True
        return request.user.is_moderator


class IsVerifiedCreator(BasePermission):
    """Only verified creators may perform this action."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_creator
            and request.user.is_verified
        )
