from rest_framework.throttling import ScopedRateThrottle


# ---------------------------------------------------------------------------
# Custom scoped throttle classes for sensitive endpoints.
# Rates are configured via settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].
# ScopedRateThrottle uses a per-user cache key for authenticated requests and
# a per-IP cache key for anonymous requests.
# ---------------------------------------------------------------------------


class LoginRateThrottle(ScopedRateThrottle):
    """Strict per-IP/user limit on login attempts to mitigate brute-force attacks."""

    scope = "login"


class RegisterRateThrottle(ScopedRateThrottle):
    """Limit new account registrations to prevent automated account-creation spam."""

    scope = "register"


class PasswordResetRateThrottle(ScopedRateThrottle):
    """Limit password-reset requests to prevent email flooding and code enumeration."""

    scope = "password_reset"


class TokenRefreshRateThrottle(ScopedRateThrottle):
    """Limit token-refresh calls to reduce token-farming and session-abuse risk."""

    scope = "token_refresh"


class InventoryWriteRateThrottle(ScopedRateThrottle):
    """Limit write operations (create / update / delete) on inventory items."""

    scope = "inventory_write"
