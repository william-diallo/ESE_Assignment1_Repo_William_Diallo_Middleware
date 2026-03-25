from django.db.models import Q
from .models import InventoryItem


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