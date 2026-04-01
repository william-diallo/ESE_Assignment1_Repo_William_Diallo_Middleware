from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

# ---------------------------------------------------------------------------
# Custom throttle classes for sensitive endpoints.
# Rates are configured via settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].
#
# AnonRateThrottle -> keys by IP for unauthenticated clients.
# UserRateThrottle -> keys by user ID for authenticated clients.
# ---------------------------------------------------------------------------


class LoginRateThrottle(AnonRateThrottle):
    """Strict per-IP limit on login attempts to mitigate brute-force attacks."""

    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    """Limit new account registrations to prevent automated account-creation spam."""

    scope = "register"


class PasswordResetRateThrottle(AnonRateThrottle):
    """Limit password-reset requests to prevent email flooding and code enumeration."""

    scope = "password_reset"


class TokenRefreshRateThrottle(AnonRateThrottle):
    """Limit token-refresh calls to reduce token-farming and session-abuse risk."""

    scope = "token_refresh"


class InventoryWriteRateThrottle(UserRateThrottle):
    """Limit write operations (create / update / delete) on inventory items."""

    scope = "inventory_write"


class ProfileRateThrottle(UserRateThrottle):
    """Limit requests to the authenticated profile endpoint."""

    scope = "profile"
