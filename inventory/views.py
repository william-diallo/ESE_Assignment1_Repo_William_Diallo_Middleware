from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from accounts.permissions import IsStaffOrReadOnly

from .models import InventoryItem
from .serialisers import InventoryItemSerializer
from .services import search_inventory_items


class InventoryItemViewSet(viewsets.ModelViewSet):
    """API endpoint that allows inventory items to be viewed or edited."""

    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer

    def get_permissions(self):
        # Allow anyone to create inventory items (POST), similar to the account register endpoint.
        if self.action == "create":
            return [AllowAny()]

        # For all other actions (list/retrieve/update/delete), enforce staff/read logic.
        return [IsStaffOrReadOnly()]

    def get_queryset(self):
        queryset = InventoryItem.objects.all()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = search_inventory_items(search_query)
        return queryset
