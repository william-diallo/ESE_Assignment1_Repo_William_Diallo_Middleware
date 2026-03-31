"""Email service module for sending notifications via SendGrid.

This module handles all email communications in the Inventory Management System,
particularly focusing on low stock alert emails sent to admin users.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import List
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def send_low_stock_alert_email(item):
    """
    Send an email alert to all admin users when an inventory item reaches low stock.

    This function is triggered when an item's quantity drops below the LOW_STOCK_THRESHOLD.
    It retrieves all admin/staff users and sends them a formatted email alert via SendGrid
    containing details about the low stock item.

    Args:
        item: InventoryItem instance object that has reached low stock status

    Returns:
        bool: True if email was sent successfully, False otherwise

    Raises:
        Exception: If SendGrid API call fails (logged but not re-raised)
    """

    # Verify that SendGrid API key is configured
    if not settings.SENDGRID_API_KEY:
        logger.warning(
            f"SendGrid API key not configured. Low stock alert for '{item.name}' "
            "was not sent. Please set SENDGRID_API_KEY in environment variables."
        )
        return False

    try:
        # Retrieve all admin and staff users who should receive the notification
        # Using filter to get users with is_staff=True (includes both admins and staff)
        admin_emails = _get_admin_emails()

        if not admin_emails:
            logger.warning(
                f"No admin users found. Low stock alert for '{item.name}' was not sent."
            )
            return False

        # Compose the email subject and body with item details
        subject = f"LOW STOCK ALERT: {item.name}"
        html_content = _generate_low_stock_email_html(item)
        text_content = _generate_low_stock_email_text(item)

        # Send email to each admin user
        for admin_email in admin_emails:
            _send_email_via_sendgrid(
                to_email=admin_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content,
            )

        logger.info(
            f"Low stock alert sent successfully for '{item.name}' to {len(admin_emails)} admin user(s)"
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to send low stock alert for '{item.name}': {str(e)}"
        )
        return False


def send_password_reset_code_email(user_email: str, code: str, expiry_minutes: int) -> bool:
    """Send a password reset verification code to a single user email."""

    if not settings.SENDGRID_API_KEY:
        logger.warning(
            "SendGrid API key not configured. Password reset code email was not sent."
        )
        return False

    try:
        subject = "Password Reset Verification"
        html_content = _generate_password_reset_email_html(code, expiry_minutes)
        _send_email_via_sendgrid(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
        )
        logger.info(f"Password reset code email sent to {user_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset code to {user_email}: {str(e)}")
        return False


def _get_admin_emails() -> List[str]:
    """
    Retrieve all admin-level user email addresses.

    Returns:
        List[str]: Unique email addresses for admin-level users.
    """
    # Admin-level users are users explicitly marked ADMIN by role,
    # plus privileged Django users (staff/superuser).
    admin_users = User.objects.filter(
        Q(role="ADMIN") | Q(is_staff=True) | Q(is_superuser=True)
    ).exclude(email="").values_list("email", flat=True).distinct()
    return list(admin_users)


def _generate_low_stock_email_html(item) -> str:
    """
    Generate a formatted HTML email body for the low stock alert.

    Creates a professional-looking email template with item details,
    current quantity, and a call-to-action for the admin to review.

    Args:
        item: InventoryItem instance with low stock status

    Returns:
        str: HTML formatted email content
    """
    # Create an HTML email template with item details
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .alert-header {{ background-color: #ff6b6b; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .item-details {{ background-color: #f5f5f5; padding: 15px; border-left: 4px solid #ff6b6b; margin: 15px 0; }}
                .detail-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #666; }}
                .value {{ color: #333; }}
                .cta-button {{ display: inline-block; background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
                .footer {{ font-size: 12px; color: #999; margin-top: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert-header">
                    <h2>⚠️  Inventory Alert: Low Stock Notification</h2>
                </div>

                <p>Hello,</p>
                <p>An inventory item has reached <strong>low stock</strong> status and requires attention.</p>

                <div class="item-details">
                    <div class="detail-row">
                        <span class="label">Item Name:</span>
                        <span class="value">{item.name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Category:</span>
                        <span class="value">{item.category or 'Not specified'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Current Quantity:</span>
                        <span class="value" style="color: #ff6b6b; font-weight: bold;">{item.quantity} units</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Description:</span>
                        <span class="value">{item.description or 'No description available'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Status:</span>
                        <span class="value" style="color: #ff9800; font-weight: bold;">{item.status}</span>
                    </div>
                </div>

                <p>Please log in to the admin panel to review inventory levels and place a reorder if necessary.</p>

                <a href="{settings.ADMIN_PANEL_URL}" class="cta-button">View in Admin Panel</a>

                <div class="footer">
                    <p>This is an automated notification from the Inventory Management System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
    </html>
    """
    return html_content


def _send_email_via_sendgrid(
    to_email: str,
    subject: str,
    html_content: str,
    plain_text_content: str | None = None,
) -> bool:
    """
    Send an email using the SendGrid API.

    This is a low-level function that handles the actual SendGrid API call.

    Args:
        to_email (str): Recipient email address
        subject (str): Email subject line
        html_content (str): HTML formatted email body

    Returns:
        bool: True if email was sent successfully, False otherwise

    Raises:
        Exception: If SendGrid API call fails
    """
    try:
        # Initialize SendGrid client with API key from settings
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

        # Create Mail object with sender, recipient, subject, and HTML content
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text_content,
        )

        # Send the email via SendGrid API
        response = sg.send(message)
        message_id = response.headers.get("X-Message-Id") if response.headers else None
        logger.info(
            "SendGrid accepted email to %s with status %s (message_id=%s)",
            to_email,
            response.status_code,
            message_id,
        )

        # SendGrid returns status code 202 for successful email acceptance
        return response.status_code == 202

    except Exception as e:
        logger.error(f"SendGrid API error while sending to {to_email}: {str(e)}")
        raise


def _generate_password_reset_email_html(code: str, expiry_minutes: int) -> str:
    """Generate minimal HTML body matching the test.py email style."""
    return (
        f"<strong>Your password reset code is {code}. "
        f"It expires in {expiry_minutes} minutes.</strong>"
    )


def _generate_low_stock_email_text(item) -> str:
    """Generate plain-text body for low stock alerts."""
    return (
        "Inventory Alert: Low Stock Notification\n\n"
        "An inventory item has reached low stock status and requires attention.\n\n"
        f"Item Name: {item.name}\n"
        f"Category: {item.category or 'Not specified'}\n"
        f"Current Quantity: {item.quantity} units\n"
        f"Description: {item.description or 'No description available'}\n"
        f"Status: {item.status}\n\n"
        "Please review inventory levels and place a reorder if necessary.\n"
    )
