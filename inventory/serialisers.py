from rest_framework import serializers

from .models import InventoryItem


class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for inventory items.

    Allows clients to create items by supplying the required fields and adds
    computed fields (like `status`) automatically.

    Automatically sets the `created_by` field from the requesting user.
    """

    # Expose the internal `quantity` field as `quantity` in the API payload.
    quantity = serializers.IntegerField()

    # Status is derived from the quantity (computed property on the model).
    status = serializers.CharField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = (
            "id",
            "name",
            "description",
            "quantity",
            "category",
            "status",
            "created_at",
            "updated_at",
            "created_by",
        )
        read_only_fields = ("id", "created_at", "updated_at", "created_by", "status")

    def create(self, validated_data):
        # Store the creator's email address.
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["created_by"] = request.user.email
        return super().create(validated_data)


class InventoryItemUpdateSerializer(serializers.ModelSerializer):
    """Serializer used for updating editable inventory item attributes."""

    quantity = serializers.IntegerField(min_value=0, required=False)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = (
            "id",
            "name",
            "description",
            "quantity",
            "category",
            "status",
            "created_at",
            "updated_at",
            "created_by",
        )
        read_only_fields = ("id", "created_at", "updated_at", "created_by", "status")
