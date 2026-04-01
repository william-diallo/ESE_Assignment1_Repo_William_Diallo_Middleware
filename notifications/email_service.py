"""Backward-compatible notification API re-export module."""

from .workflows import (
    send_low_stock_alert_email,
    send_password_reset_code_email,
    send_password_reset_success_email,
)

__all__ = [
    "send_low_stock_alert_email",
    "send_password_reset_code_email",
    "send_password_reset_success_email",
]
