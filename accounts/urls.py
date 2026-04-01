from django.urls import path

from .views import (
    CaseInsensitiveTokenObtainPairView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    ThrottledTokenRefreshView,
)

urlpatterns = [
    # User registration
    path("register/", RegisterView.as_view(), name="register"),
    # JWT authentication endpoints
    path("login/", CaseInsensitiveTokenObtainPairView.as_view(), name="login"),
    path("refresh/", ThrottledTokenRefreshView.as_view(), name="token_refresh"),
    # Profile endpoint (requires a valid access token)
    path("me/", ProfileView.as_view(), name="profile"),
    # Password reset flow: request a code and confirm it with a new password
    path(
        "password-reset/request/",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
