from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import InventoryItem
from .serialisers import InventoryItemSerializer
from accounts.permissions import IsStaffOrReadOnly


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
