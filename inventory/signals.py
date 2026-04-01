import json
import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from notifications.workflows import send_low_stock_alert_email

from .models import InventoryItem

audit_logger = logging.getLogger("inventory.audit")


def _serialize_item(item: InventoryItem) -> dict:
    """Return a complete, JSON-serializable snapshot of an inventory item."""

    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "quantity": item.quantity,
        "category": item.category,
        "created_by": item.created_by,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        "status": item.stock_status,
    }


@receiver(pre_save, sender=InventoryItem)
def cache_previous_stock_status(sender, instance: InventoryItem, **kwargs):
    """Track previous item state so transitions and audit updates can be detected."""

    if not instance.pk:
        instance._previous_stock_status = None
        instance._previous_item_data = None
        return

    try:
        previous_item = InventoryItem.objects.get(pk=instance.pk)
        instance._previous_stock_status = previous_item.stock_status
        instance._previous_item_data = _serialize_item(previous_item)
    except InventoryItem.DoesNotExist:
        instance._previous_stock_status = None
        instance._previous_item_data = None


@receiver(post_save, sender=InventoryItem)
def notify_low_stock_on_status_change(
    sender,
    instance: InventoryItem,
    created: bool,
    **kwargs,
):
    """Send an alert only when an item enters LOW_STOCK from another state."""

    current_item_data = _serialize_item(instance)
    event_timestamp = timezone.now().isoformat()

    if created:
        audit_logger.info(
            "date : %s, Added: %s",
            event_timestamp,
            json.dumps(current_item_data, ensure_ascii=True),
        )
        return

    previous_status = getattr(instance, "_previous_stock_status", None)
    current_status = instance.stock_status

    # Fire exactly on transition into LOW_STOCK after an update.
    if (
        current_status == InventoryItem.STATUS_LOW_STOCK
        and previous_status != InventoryItem.STATUS_LOW_STOCK  # noqa: W503
    ):
        send_low_stock_alert_email(instance)

    previous_item_data = getattr(instance, "_previous_item_data", None)
    if previous_item_data is None:
        previous_item_data = {}

    audit_logger.info(
        "date : %s, Initial Item: %s, updated Item: %s",
        event_timestamp,
        json.dumps(previous_item_data, ensure_ascii=True),
        json.dumps(current_item_data, ensure_ascii=True),
    )


@receiver(post_delete, sender=InventoryItem)
def log_inventory_item_deletion(sender, instance: InventoryItem, **kwargs):
    """Write deletion audit entries for inventory items."""

    event_timestamp = timezone.now().isoformat()
    deleted_item_data = _serialize_item(instance)
    audit_logger.info(
        "date : %s, deleted: %s",
        event_timestamp,
        json.dumps(deleted_item_data, ensure_ascii=True),
    )
