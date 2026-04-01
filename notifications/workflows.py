"""Business workflows for outbound notifications."""

import logging

from .recipients import get_admin_emails
from .templates import (
    generate_low_stock_email_html,
    generate_low_stock_email_text,
    generate_password_reset_email_html,
    generate_password_reset_success_email_html,
    generate_password_reset_success_email_text,
)
from .transports import get_setting, send_email_via_sendgrid

logger = logging.getLogger(__name__)


def send_low_stock_alert_email(item):
    """Send a low-stock alert to all privileged recipients."""

    if not get_setting("SENDGRID_API_KEY"):
        logger.warning(
            "SendGrid API key not configured. Low stock alert for '%s' was not sent. "
            "Please set SENDGRID_API_KEY in environment variables.",
            item.name,
        )
        return False

    try:
        admin_emails = get_admin_emails()
        if not admin_emails:
            logger.warning(
                "No admin users found. Low stock alert for '%s' was not sent.",
                item.name,
            )
            return False

        subject = f"LOW STOCK ALERT: {item.name}"
        html_content = generate_low_stock_email_html(item)
        text_content = generate_low_stock_email_text(item)

        for admin_email in admin_emails:
            send_email_via_sendgrid(
                to_email=admin_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content,
            )

        logger.info(
            "Low stock alert sent successfully for '%s' to %s admin user(s)",
            item.name,
            len(admin_emails),
        )
        return True
    except Exception as exc:
        logger.error("Failed to send low stock alert for '%s': %s", item.name, str(exc))
        return False


def send_password_reset_code_email(
    user_email: str, code: str, expiry_minutes: int
) -> bool:
    """Send a password reset verification code to a single user email."""

    if not get_setting("SENDGRID_API_KEY"):
        logger.warning(
            "SendGrid API key not configured. Password reset code email was not sent."
        )
        return False

    try:
        send_email_via_sendgrid(
            to_email=user_email,
            subject="Password Reset Verification",
            html_content=generate_password_reset_email_html(code, expiry_minutes),
        )
        logger.info("Password reset code email sent to %s", user_email)
        return True
    except Exception as exc:
        logger.error("Failed to send password reset code to %s: %s", user_email, str(exc))
        return False


def send_password_reset_success_email(user_email: str) -> bool:
    """Send a confirmation email after a user's password has been reset."""

    if not get_setting("SENDGRID_API_KEY"):
        logger.warning(
            "SendGrid API key not configured. Password reset success email was not sent."
        )
        return False

    try:
        send_email_via_sendgrid(
            to_email=user_email,
            subject="Your Password Was Reset",
            html_content=generate_password_reset_success_email_html(),
            plain_text_content=generate_password_reset_success_email_text(),
        )
        logger.info("Password reset confirmation email sent to %s", user_email)
        return True
    except Exception as exc:
        logger.error(
            "Failed to send password reset confirmation to %s: %s",
            user_email,
            str(exc),
        )
        return False
