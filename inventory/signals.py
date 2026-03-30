from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from notifications.email_service import send_low_stock_alert_email

from .models import InventoryItem


@receiver(pre_save, sender=InventoryItem)
def cache_previous_stock_status(sender, instance: InventoryItem, **kwargs):
    """Track the previous stock status so transitions can be detected after save."""

    if not instance.pk:
        instance._previous_stock_status = None
        return

    try:
        previous_item = InventoryItem.objects.get(pk=instance.pk)
        instance._previous_stock_status = previous_item.stock_status
    except InventoryItem.DoesNotExist:
        instance._previous_stock_status = None


@receiver(post_save, sender=InventoryItem)
def notify_low_stock_on_status_change(
    sender,
    instance: InventoryItem,
    created: bool,
    **kwargs,
):
    """Send an alert only when an item enters LOW_STOCK from another state."""

    # The requirement is update-driven alerts, not creation-time alerts.
    if created:
        return

    previous_status = getattr(instance, "_previous_stock_status", None)
    current_status = instance.stock_status

    # Fire exactly on transition into LOW_STOCK after an update.
    if (
        current_status == InventoryItem.STATUS_LOW_STOCK
        and previous_status != InventoryItem.STATUS_LOW_STOCK
    ):
        send_low_stock_alert_email(instance)
