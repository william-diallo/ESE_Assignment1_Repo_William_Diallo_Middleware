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


    # Optionally link the item to the user who created it.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_items",
        help_text="User who created this inventory item.",
    )


    class Meta:
        ordering = ["-updated_at"]


    @property
    def status(self) -> str:
        """Return a high-level stock status derived from the current quantity."""

        if self.quantity == 0:
            return self.STATUS_OUT_OF_STOCK
        if self.quantity < 10:
            return self.STATUS_LOW_STOCK
        return self.STATUS_AVAILABLE


    def __str__(self):
        return f"{self.name} (qty={self.quantity})"