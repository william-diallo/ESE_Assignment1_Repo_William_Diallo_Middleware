"""Application services for account workflows."""

import random
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from notifications.workflows import (
    send_password_reset_code_email,
    send_password_reset_success_email,
)

from .models import PasswordResetCode, User


@dataclass(frozen=True)
class PasswordResetRequestResult:
    """Outcome of a password reset request workflow."""

    email_matched: bool
    email_sent: bool


@dataclass(frozen=True)
class PasswordResetConfirmResult:
    """Outcome of a password reset confirmation workflow."""

    confirmation_email_sent: bool


def request_password_reset(email: str) -> PasswordResetRequestResult:
    """Create a new password reset code and attempt email delivery."""

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return PasswordResetRequestResult(email_matched=False, email_sent=False)

    PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

    code = f"{random.randint(0, 999999):06d}"
    expiry_minutes = int(getattr(settings, "PASSWORD_RESET_CODE_EXPIRY_MINUTES", 10))
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

    PasswordResetCode.objects.create(user=user, code=code, expires_at=expires_at)

    email_sent = send_password_reset_code_email(
        user_email=user.email,
        code=code,
        expiry_minutes=expiry_minutes,
    )
    return PasswordResetRequestResult(email_matched=True, email_sent=email_sent)


def confirm_password_reset(
    *, user: User, reset_code: PasswordResetCode, new_password: str
) -> PasswordResetConfirmResult:
    """Persist a new password and invalidate any remaining reset codes."""

    user.set_password(new_password)
    user.save(update_fields=["password"])

    reset_code.is_used = True
    reset_code.save(update_fields=["is_used"])
    PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

    confirmation_email_sent = send_password_reset_success_email(user.email)
    return PasswordResetConfirmResult(confirmation_email_sent=confirmation_email_sent)
