from django.conf import settings
from django.db import models


class InventoryItem(models.Model):
    """Represents a single item in the inventory.

    The `id` primary key is automatically provided by Django.
    """

    STATUS_AVAILABLE = "AVAILABLE"
    STATUS_LOW_STOCK = "LOW_STOCK"
    STATUS_OUT_OF_STOCK = "OUT_OF_STOCK"

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "Available"),
        (STATUS_LOW_STOCK, "Low stock"),
        (STATUS_OUT_OF_STOCK, "Out of stock"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=0)

    # Category is a simple string in this model; a separate Category model could be added later.
    category = models.CharField(max_length=100, blank=True)

    # Track creation / update timestamps.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Store the email of the user who created this item.
    created_by = models.EmailField(
        null=True,
        blank=True,
        help_text="Email of the user who created this inventory item.",
    )

    class Meta:
        db_table = "inventory_items"
        ordering = ["-updated_at"]
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"

    @property
    def stock_status(self) -> str:
        """Return a high-level stock status derived from the current quantity."""

        low_stock_threshold = max(getattr(settings, "LOW_STOCK_THRESHOLD", 10), 1)

        if self.quantity == 0:
            return self.STATUS_OUT_OF_STOCK
        if self.quantity < low_stock_threshold:
            return self.STATUS_LOW_STOCK
        return self.STATUS_AVAILABLE

    @property
    def status(self) -> str:
        """Backward-compatible alias for computed stock status."""

        return self.stock_status

    def __str__(self):
        return f"{self.name} (qty={self.quantity})"
