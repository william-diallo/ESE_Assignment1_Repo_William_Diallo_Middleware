from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from accounts.permissions import IsStaffOrReadOnly
from .models import InventoryItem
from .serialisers import InventoryItemSerializer
from .services import search_inventory_items, create_inventory_item
from django.core.exceptions import PermissionDenied


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer

    def get_permissions(self):
        # Only staff can create items
        if self.action == "create":
            return [IsStaffOrReadOnly()]

        return [IsStaffOrReadOnly()]

    def create(self, request, *args, **kwargs):
        """Create an inventory item only if the user is an admin."""
        try:
            item = create_inventory_item(
                user=request.user,
                name=request.data.get("name"),
                description=request.data.get("description"),
                category=request.data.get("category"),
                quantity=request.data.get("quantity"),
            )

            serializer = self.get_serializer(item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PermissionDenied:
            return Response(
                {"detail": "Only admin users can create inventory items."},
                status=status.HTTP_403_FORBIDDEN,
            )

    def get_queryset(self):
        queryset = InventoryItem.objects.all()
        search_query = self.request.query_params.get("search", None)
        if search_query:
            queryset = search_inventory_items(search_query)
        return queryset
