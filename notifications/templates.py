"""Notification email content builders."""

from .transports import get_setting


def generate_low_stock_email_html(item) -> str:
    """Generate HTML content for low-stock notifications."""

    return f"""
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

                <a href="{get_setting('ADMIN_PANEL_URL', '#')}" class="cta-button">View in Admin Panel</a>

                <div class="footer">
                    <p>This is an automated notification from the Inventory Management System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
    </html>
    """


def generate_low_stock_email_text(item) -> str:
    """Generate plain-text content for low-stock notifications."""

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


def generate_password_reset_email_html(code: str, expiry_minutes: int) -> str:
    """Generate minimal HTML body for password reset code delivery."""

    return (
        f"<strong>Your password reset code is {code}. "
        f"It expires in {expiry_minutes} minutes.</strong>"
    )


def generate_password_reset_success_email_html() -> str:
    """Generate HTML content for password-reset completion confirmation."""

    return (
        "<strong>Your password was reset successfully.</strong>"
        "<br><br>If you did not make this change, please secure your account immediately."
    )


def generate_password_reset_success_email_text() -> str:
    """Generate plain-text content for password-reset completion confirmation."""

    return (
        "Your password was reset successfully.\n\n"
        "If you did not make this change, please secure your account immediately.\n"
    )