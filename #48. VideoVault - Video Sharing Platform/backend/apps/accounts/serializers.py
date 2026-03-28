"""
Serializers for the accounts app.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "password", "password_confirm",
            "role", "bio", "date_of_birth",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        # Only allow viewer/creator on self-registration
        role = attrs.get("role", User.Role.VIEWER)
        if role not in (User.Role.VIEWER, User.Role.CREATOR):
            raise serializers.ValidationError(
                {"role": "You can only register as a viewer or creator."}
            )
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Read/update serializer for user profiles."""
    subscriber_count = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "role", "avatar", "banner",
            "bio", "website", "date_of_birth", "is_verified",
            "twitter_url", "instagram_url",
            "subscriber_count", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "email", "role", "is_verified",
            "subscriber_count", "created_at", "updated_at",
        ]


class UserPublicSerializer(serializers.ModelSerializer):
    """Minimal public serializer for embedding user info in other responses."""
    subscriber_count = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id", "username", "avatar", "is_verified", "subscriber_count",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add custom claims to JWT tokens."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = user.role
        token["is_verified"] = user.is_verified
        return token

    def validate(self, attrs):
        # Accept email as the username field
        data = super().validate(attrs)
        data["user"] = UserPublicSerializer(self.user).data
        return data
