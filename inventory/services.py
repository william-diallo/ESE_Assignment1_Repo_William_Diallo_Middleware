from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from .models import InventoryItem


def _is_admin_user(user) -> bool:
    """Return True when user has admin/staff privileges for inventory writes."""

    user_role = str(getattr(user, "role", "")).upper()
    return user.is_staff or user.is_superuser or user_role in {"ADMIN", "STAFF"}


def search_inventory_items(query):
    """
    Search for inventory items based on name, description, ID, or category.

    Args:
        query (str): The search query string.

    Returns:
        QuerySet: A queryset of InventoryItem objects that match the search criteria.
    """
    if not query:
        return InventoryItem.objects.none()

    # Create a Q object for OR conditions
    search_filter = Q()

    # Search by name (case-insensitive)
    search_filter |= Q(name__icontains=query)

    # Search by description (case-insensitive)
    search_filter |= Q(description__icontains=query)

    # Search by category (case-insensitive)
    search_filter |= Q(category__icontains=query)

    # Try to search by ID if query is numeric
    try:
        item_id = int(query)
        search_filter |= Q(id=item_id)
    except ValueError:
        pass  # query is not a valid integer, skip ID search

    return InventoryItem.objects.filter(search_filter)


def create_inventory_item(user, name, description, category, quantity):
    """
    Create an InventoryItem only if the user is an admin (staff or superuser).

    Args:
        user (User): The user attempting to create the item.
        name (str): Item name.
        description (str): Item description.
        category (str): Item category.
        quantity (int): Quantity in stock.

    Returns:
        InventoryItem: The created inventory item.

    Raises:
        PermissionDenied: If the user is not an admin.
    """

    if not _is_admin_user(user):
        raise PermissionDenied("Only admin users can create inventory items.")

    try:
        quantity_value = int(quantity)
    except (TypeError, ValueError):
        raise ValidationError("Quantity must be a valid integer.")

    if quantity_value < 0:
        raise ValidationError("Quantity cannot be negative.")

    return InventoryItem.objects.create(
        name=name,
        description=description,
        category=category,
        quantity=quantity_value,
        created_by=getattr(user, "email", None),
    )


def update_inventory_item(user, item: InventoryItem, **fields):
    """
    Update an InventoryItem only if the user is an admin.
    """
    if not _is_admin_user(user):
        raise PermissionDenied("Only admin users can update inventory items.")

    allowed_fields = {"name", "description", "category", "quantity"}
    invalid_fields = set(fields) - allowed_fields
    if invalid_fields:
        raise ValidationError(
            f"Invalid field(s) for update: {', '.join(sorted(invalid_fields))}."
        )

    if "quantity" in fields:
        try:
            quantity_value = int(fields["quantity"])
        except (TypeError, ValueError):
            raise ValidationError("Quantity must be a valid integer.")

        if quantity_value < 0:
            raise ValidationError("Quantity cannot be negative.")

        fields["quantity"] = quantity_value

    for field, value in fields.items():
        setattr(item, field, value)

    item.save()
    return item


def delete_inventory_item(user, item: InventoryItem):
    """
    Delete an InventoryItem only if the user is an admin.
    """
    if not _is_admin_user(user):
        raise PermissionDenied("Only admin users can delete inventory items.")

    item.delete()
    return True
