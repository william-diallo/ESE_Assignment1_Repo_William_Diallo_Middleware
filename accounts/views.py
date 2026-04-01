from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serialisers import (
    CaseInsensitiveTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services import confirm_password_reset, request_password_reset
from .throttles import (
    LoginRateThrottle,
    PasswordResetRateThrottle,
    ProfileRateThrottle,
    RegisterRateThrottle,
    TokenRefreshRateThrottle,
)


class CaseInsensitiveTokenObtainPairView(TokenObtainPairView):
    """JWT login view that treats email matching as case-insensitive."""

    serializer_class = CaseInsensitiveTokenObtainPairSerializer
    # Strict limit to block brute-force credential guessing.
    throttle_classes = [LoginRateThrottle]


class RegisterView(generics.CreateAPIView):
    """API endpoint for registering a new user."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = []  # Allow anyone to access this endpoint
    # Prevent automated account-creation spam.
    throttle_classes = [RegisterRateThrottle]


class ProfileView(APIView):
    """API endpoint to return the currently authenticated user's profile."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ProfileRateThrottle]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ThrottledTokenRefreshView(TokenRefreshView):
    """Token refresh endpoint with rate limiting to prevent token farming."""

    # Prevents rapid re-issuance of access tokens from long-lived refresh tokens.
    throttle_classes = [TokenRefreshRateThrottle]


class PasswordResetRequestView(APIView):
    """Send a one-time code to the user's email for password reset."""

    permission_classes = []
    # Prevent email flooding and OTP code enumeration.
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        request_result = request_password_reset(email)
        generic_response = {
            "detail": "If an account with that email exists, a reset code has been sent."
        }

        if not request_result.email_matched:
            response_data = dict(generic_response)
            if settings.DEBUG:
                response_data["email_matched"] = False
            return Response(response_data, status=status.HTTP_200_OK)

        if not request_result.email_sent and settings.DEBUG:
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
            response_data["email_sent"] = request_result.email_sent
        return Response(response_data, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Verify code and replace the user's old password with the new one."""

    permission_classes = []
    # Same scope as the request view — share the per-user/IP budget.
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        reset_code = serializer.validated_data["reset_code"]
        new_password = serializer.validated_data["new_password"]
        confirm_result = confirm_password_reset(
            user=user,
            reset_code=reset_code,
            new_password=new_password,
        )

        response_data = {"detail": "Password has been reset successfully."}
        if settings.DEBUG:
            response_data["confirmation_email_sent"] = (
                confirm_result.confirmation_email_sent
            )
        return Response(response_data, status=status.HTTP_200_OK)
