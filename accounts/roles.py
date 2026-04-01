"""Shared role and authorization helpers for account-aware modules."""

PRIVILEGED_ROLES = {"ADMIN", "STAFF"}


def get_normalized_role(user_or_role) -> str:
    """Return an uppercase role string from either a user object or raw role."""

    if isinstance(user_or_role, str):
        return user_or_role.strip().upper()

    return str(getattr(user_or_role, "role", "")).strip().upper()


def has_privileged_role(user) -> bool:
    """Return True when a user should be allowed privileged staff actions."""

    if not user:
        return False

    return bool(
        getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
        or get_normalized_role(user) in PRIVILEGED_ROLES
    )