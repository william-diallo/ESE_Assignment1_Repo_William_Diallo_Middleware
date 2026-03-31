from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import PasswordResetCode, User


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration.


    This serializer validates incoming registration data, hashes the password,
    and creates a new user instance.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("email", "password", "role")

    def create(self, validated_data):
        # Create the user with a hashed password
        user = User.objects.create(
            email=validated_data["email"],
            role=validated_data.get("role", "STAFF"),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class CaseInsensitiveTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Authenticate using email case-insensitively for JWT login."""

    def validate(self, attrs):
        email = attrs.get(self.username_field)
        if isinstance(email, str):
            normalized_email = email.strip()
            user = User.objects.filter(email__iexact=normalized_email).first()
            if user:
                # Use canonical stored email so Django authentication can match.
                attrs[self.username_field] = user.email
            else:
                attrs[self.username_field] = normalized_email

        return super().validate(attrs)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for reading user profile data."""

    class Meta:
        model = User
        fields = ("id", "email", "role", "is_active", "is_staff", "date_joined")
        read_only_fields = ("id", "is_active", "is_staff", "date_joined")


class PasswordResetRequestSerializer(serializers.Serializer):
    """Input serializer for requesting a reset code to be sent by email."""

    email = serializers.EmailField()

    def validate_email(self, value):
        # Normalize leading/trailing whitespace before lookup.
        return value.strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Input serializer for confirming reset code and setting a new password."""

    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )

    def validate_email(self, value):
        # Normalize leading/trailing whitespace before lookup.
        return value.strip()

    def validate(self, attrs):
        email = attrs["email"]
        code = attrs["code"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"email": "No account found for this email."}
            ) from exc

        # Grab the latest unused matching code for this user.
        reset_code = (
            PasswordResetCode.objects.filter(user=user, code=code, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if not reset_code:
            raise serializers.ValidationError({"code": "Invalid reset code."})

        if reset_code.is_expired:
            raise serializers.ValidationError({"code": "This reset code has expired."})

        attrs["user"] = user
        attrs["reset_code"] = reset_code
        return attrs
