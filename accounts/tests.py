from datetime import timedelta
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from accounts.middleware import RequestLoggingMiddleware
from accounts.models import PasswordResetCode
from accounts.permissions import AllowAnonymousCreate, IsStaffOrReadOnly
from accounts.serialisers import PasswordResetConfirmSerializer, RegisterSerializer
from notifications.email_service import send_password_reset_success_email
from tests.utils import create_test_user


class UserAndResetCodeModelTests(TestCase):
    """Unit tests for account-related model behavior."""

    def test_password_reset_code_is_expired_false_before_expiry(self):
        # Create a code that expires in the future.
        user = create_test_user(email="model@example.com", password="TestPass123!")
        reset_code = PasswordResetCode.objects.create(
            user=user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        self.assertFalse(reset_code.is_expired)

    def test_password_reset_code_is_expired_true_after_expiry(self):
        # Create a code that already expired.
        user = create_test_user(email="expired@example.com", password="TestPass123!")
        reset_code = PasswordResetCode.objects.create(
            user=user,
            code="654321",
            expires_at=timezone.now() - timedelta(minutes=5),
        )

        self.assertTrue(reset_code.is_expired)


class PermissionClassTests(TestCase):
    """Unit tests for custom DRF permission classes."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.staff_user = create_test_user(
            email="staff@example.com", password="TestPass123!", role="STAFF"
        )
        self.admin_user = create_test_user(
            email="admin@example.com", password="TestPass123!", role="ADMIN"
        )
        self.regular_user = create_test_user(
            email="user@example.com", password="TestPass123!", role="STAFF"
        )
        # Simulate a non-privileged role for the write-permission checks.
        self.regular_user.role = "VIEWER"

    def test_is_staff_or_read_only_allows_safe_method_for_authenticated_user(self):
        request = self.factory.get("/api/inventory/items/")
        request.user = self.regular_user

        permission = IsStaffOrReadOnly()
        self.assertTrue(permission.has_permission(request, view=None))

    def test_is_staff_or_read_only_blocks_write_for_non_admin_role(self):
        request = self.factory.post("/api/inventory/items/", {})
        request.user = self.regular_user

        permission = IsStaffOrReadOnly()
        self.assertFalse(permission.has_permission(request, view=None))

    def test_allow_anonymous_create_allows_post_without_auth(self):
        request = self.factory.post("/api/auth/register/", {})
        request.user = type("AnonymousUser", (), {"is_authenticated": False})()

        permission = AllowAnonymousCreate()
        self.assertTrue(permission.has_permission(request, view=None))


class SerializerUnitTests(TestCase):
    """Unit tests for account serializers."""

    def test_register_serializer_hashes_password(self):
        # Registration should never store raw plaintext passwords.
        serializer = RegisterSerializer(
            data={
                "email": "serializer@example.com",
                "password": "ComplexPass123!",
                "role": "STAFF",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()
        self.assertTrue(user.check_password("ComplexPass123!"))
        self.assertNotEqual(user.password, "ComplexPass123!")

    def test_password_reset_confirm_serializer_rejects_invalid_code(self):
        user = create_test_user(email="confirm@example.com", password="TestPass123!")
        PasswordResetCode.objects.create(
            user=user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        serializer = PasswordResetConfirmSerializer(
            data={
                "email": "confirm@example.com",
                "code": "000000",
                "new_password": "AnotherPass123!",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)


class MiddlewareUnitTests(TestCase):
    """Unit tests for request logging middleware behavior."""

    def setUp(self):
        self.middleware = RequestLoggingMiddleware(
            get_response=lambda request: HttpResponse("ok")
        )
        self.factory = RequestFactory()

    def test_middleware_echoes_x_request_id_header(self):
        # Incoming request ID should be echoed in API responses.
        request = self.factory.get("/api/auth/me/", HTTP_X_REQUEST_ID="abc-123")
        self.middleware.process_request(request)

        response = HttpResponse("ok")
        response = self.middleware.process_response(request, response)

        self.assertEqual(response["X-Request-ID"], "abc-123")


class PasswordResetViewUnitTests(TestCase):
    """Unit tests for password reset endpoint behavior."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(
            email="resetuser@example.com", password="OldPass123!", role="STAFF"
        )

    @patch("accounts.services.send_password_reset_code_email", return_value=True)
    def test_password_reset_request_unknown_email_returns_generic_success(
        self, mocked_sender
    ):
        # Unknown emails should still return a generic 200 to prevent enumeration.
        response = self.client.post(
            "/api/auth/password-reset/request/",
            {"email": "doesnotexist@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "If an account with that email exists, a reset code has been sent.",
        )
        mocked_sender.assert_not_called()

    @patch("accounts.services.send_password_reset_success_email", return_value=True)
    def test_password_reset_confirm_sends_success_email(
        self, mocked_confirmation_sender
    ):
        # A valid code should reset password and trigger confirmation email.
        reset_code = PasswordResetCode.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            {
                "email": self.user.email,
                "code": "123456",
                "new_password": "NewPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], "Password has been reset successfully."
        )
        mocked_confirmation_sender.assert_called_once_with(self.user.email)

        # Ensure old code is marked as used after reset completion.
        reset_code.refresh_from_db()
        self.assertTrue(reset_code.is_used)


class EmailServiceUnitTests(TestCase):
    """Unit tests for password reset success email helper."""

    @override_settings(SENDGRID_API_KEY="")
    def test_success_email_returns_false_without_api_key(self):
        # Missing API key should fail safely without raising.
        self.assertFalse(send_password_reset_success_email("nobody@example.com"))

    @override_settings(
        SENDGRID_API_KEY="SG.test", DEFAULT_FROM_EMAIL="sender@example.com"
    )
    @patch("notifications.workflows.send_email_via_sendgrid", return_value=True)
    def test_success_email_calls_sendgrid_helper(self, mocked_send):
        sent = send_password_reset_success_email("target@example.com")
        self.assertTrue(sent)
        mocked_send.assert_called_once()


class AuthenticationIntegrationTests(TestCase):
    """Integration tests for register, login, refresh, and profile endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_register_login_refresh_profile_flow(self):
        # 1) Register a user using the public registration endpoint.
        register_response = self.client.post(
            "/api/auth/register/",
            {
                "email": "integration@example.com",
                "password": "IntegrationPass123!",
                "role": "STAFF",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        # 2) Login using different case to verify case-insensitive auth.
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "email": "Integration@Example.com",
                "password": "IntegrationPass123!",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.assertIn("refresh", login_response.data)

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        # 3) Access profile endpoint with the issued access token.
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        profile_response = self.client.get("/api/auth/me/")
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["email"], "integration@example.com")

        # 4) Refresh access token using the refresh endpoint.
        refresh_response = self.client.post(
            "/api/auth/refresh/", {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)
