import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from notifications.email_service import send_password_reset_code_email

from .models import PasswordResetCode, User
from .serialisers import (CaseInsensitiveTokenObtainPairSerializer,
                          PasswordResetConfirmSerializer,
                          PasswordResetRequestSerializer, RegisterSerializer,
                          UserSerializer)


class CaseInsensitiveTokenObtainPairView(TokenObtainPairView):
    """JWT login view that treats email matching as case-insensitive."""

    serializer_class = CaseInsensitiveTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """API endpoint for registering a new user."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = []  # Allow anyone to access this endpoint


class ProfileView(APIView):
    """API endpoint to return the currently authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class PasswordResetRequestView(APIView):
    """Send a one-time code to the user's email for password reset."""

    permission_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        generic_response = {
            "detail": "If an account with that email exists, a reset code has been sent."
        }

        # Use a generic response for unknown emails to avoid account enumeration.
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            response_data = dict(generic_response)
            if settings.DEBUG:
                response_data["email_matched"] = False
            return Response(response_data, status=status.HTTP_200_OK)

        # Invalidate previous codes so only the newest code can be used.
        PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

        # Generate a simple six-digit code expected by the password reset page.
        code = f"{random.randint(0, 999999):06d}"
        expiry_minutes = int(getattr(settings, "PASSWORD_RESET_CODE_EXPIRY_MINUTES", 10))
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        PasswordResetCode.objects.create(user=user, code=code, expires_at=expires_at)

        email_sent = send_password_reset_code_email(
            user_email=user.email,
            code=code,
            expiry_minutes=expiry_minutes,
        )

        if not email_sent and settings.DEBUG:
            return Response(
                {
                    "detail": (
                        "Reset code was generated, but email delivery failed. "
                        "Check SENDGRID_API_KEY and sender configuration."
                    ),
                    "email_matched": True,
                    "email_sent": False,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = dict(generic_response)
        if settings.DEBUG:
            response_data["email_matched"] = True
            response_data["email_sent"] = True
        return Response(response_data, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Verify code and replace the user's old password with the new one."""

    permission_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        reset_code = serializer.validated_data["reset_code"]
        new_password = serializer.validated_data["new_password"]

        # Replace the old password with the new validated password.
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Mark this code as consumed and invalidate any leftover active codes.
        reset_code.is_used = True
        reset_code.save(update_fields=["is_used"])
        PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )
