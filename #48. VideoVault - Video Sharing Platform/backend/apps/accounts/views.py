"""
Views for the accounts app.
"""
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserPublicSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user account."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserPublicSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Obtain JWT token pair (access + refresh)."""
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """Blacklist the refresh token on logout."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PublicProfileView(generics.RetrieveAPIView):
    """View any user's public profile."""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "username"


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"detail": "Password updated successfully."},
            status=status.HTTP_200_OK,
        )


class UserListView(generics.ListAPIView):
    """Admin-only: list all users with filtering."""
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["role", "is_verified", "is_active"]
    search_fields = ["username", "email"]
    ordering_fields = ["created_at", "username"]
