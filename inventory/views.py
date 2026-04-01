from django.core.exceptions import PermissionDenied
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsStaffOrReadOnly
from accounts.throttles import InventoryWriteRateThrottle

from .models import InventoryItem
from .serialisers import InventoryItemSerializer, InventoryItemUpdateSerializer
from .services import (
    create_inventory_item,
    delete_inventory_item,
    search_inventory_items,
    update_inventory_item,
)


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return InventoryItemUpdateSerializer
        return InventoryItemSerializer

    def get_permissions(self):
        return [IsStaffOrReadOnly()]

    def _handle_write_result(self, operation, forbidden_detail):
        """Run a write operation and translate service exceptions to responses."""

        try:
            return operation()
        except PermissionDenied:
            return Response(
                {"detail": forbidden_detail},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValidationError as exc:
            return Response(
                {"detail": exc.detail if hasattr(exc, "detail") else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_throttles(self):
        # Write operations get a stricter per-user/IP budget to prevent abuse.
        # Read operations fall through to the global AnonRateThrottle / UserRateThrottle.
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [InventoryWriteRateThrottle()]
        return super().get_throttles()

    def create(self, request, *args, **kwargs):
        """Create an inventory item only if the user is an admin."""

        def operation():
            item = create_inventory_item(
                user=request.user,
                name=request.data.get("name"),
                description=request.data.get("description"),
                category=request.data.get("category"),
                quantity=request.data.get("quantity"),
            )

            serializer = self.get_serializer(item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return self._handle_write_result(
            operation,
            "Only admin users can create inventory items.",
        )

    def get_queryset(self):
        queryset = InventoryItem.objects.all()

        # Attribute-level table filters.
        name_query = self.request.query_params.get("name")
        category_query = self.request.query_params.get("category")
        description_query = self.request.query_params.get("description")

        if name_query:
            queryset = queryset.filter(name__icontains=name_query)
        if category_query:
            queryset = queryset.filter(category__icontains=category_query)
        if description_query:
            queryset = queryset.filter(description__icontains=description_query)

        search_query = self.request.query_params.get("search", None)
        if search_query:
            search_results = search_inventory_items(search_query)
            queryset = queryset.filter(id__in=search_results.values("id"))

        return queryset

    def destroy(self, request, *args, **kwargs):
        """Delete an inventory item only if the user is an admin/staff user."""
        item = self.get_object()

        def operation():
            delete_inventory_item(request.user, item)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return self._handle_write_result(
            operation,
            "Only admin users can delete inventory items.",
        )

    def update(self, request, *args, **kwargs):
        """Update all editable attributes of an inventory item (PUT)."""
        item = self.get_object()
        serializer = self.get_serializer(item, data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            updated_item = update_inventory_item(
                request.user,
                item,
                **serializer.validated_data,
            )
            response_serializer = InventoryItemSerializer(
                updated_item,
                context=self.get_serializer_context(),
            )
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return self._handle_write_result(
            operation,
            "Only admin users can update inventory items.",
        )

    def partial_update(self, request, *args, **kwargs):
        """Update selected editable attributes of an inventory item (PATCH)."""
        item = self.get_object()
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        def operation():
            updated_item = update_inventory_item(
                request.user,
                item,
                **serializer.validated_data,
            )
            response_serializer = InventoryItemSerializer(
                updated_item,
                context=self.get_serializer_context(),
            )
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return self._handle_write_result(
            operation,
            "Only admin users can update inventory items.",
        )
