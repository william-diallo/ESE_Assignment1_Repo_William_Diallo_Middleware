"""Low-level email transport helpers."""

import logging

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


def get_setting(name: str, default=""):
    """Safely read Django settings attributes that may be absent."""

    return getattr(settings, name, default)


def send_email_via_sendgrid(
    *,
    to_email: str,
    subject: str,
    html_content: str,
    plain_text_content: str | None = None,
) -> bool:
    """Send an email using SendGrid and return True on accepted delivery."""

    try:
        sg = SendGridAPIClient(get_setting("SENDGRID_API_KEY"))
        message = Mail(
            from_email=get_setting("DEFAULT_FROM_EMAIL", "webmaster@localhost"),
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text_content,
        )

        response = sg.send(message)
        message_id = response.headers.get("X-Message-Id") if response.headers else None
        logger.info(
            "SendGrid accepted email to %s with status %s (message_id=%s)",
            to_email,
            response.status_code,
            message_id,
        )
        return response.status_code == 202
    except Exception as exc:
        logger.error("SendGrid API error while sending to %s: %s", to_email, str(exc))
        raise