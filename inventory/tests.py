from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from inventory.models import InventoryItem
from inventory.services import (
    create_inventory_item,
    delete_inventory_item,
    search_inventory_items,
    update_inventory_item,
)
from tests.utils import create_test_user

User = get_user_model()


class InventoryModelUnitTests(TestCase):
    """Unit tests for inventory model computed status properties."""

    @override_settings(LOW_STOCK_THRESHOLD=10)
    def test_stock_status_out_of_stock(self):
        item = InventoryItem.objects.create(name="Cable", quantity=0)
        self.assertEqual(item.stock_status, InventoryItem.STATUS_OUT_OF_STOCK)

    @override_settings(LOW_STOCK_THRESHOLD=10)
    def test_stock_status_low_stock(self):
        item = InventoryItem.objects.create(name="Mouse", quantity=5)
        self.assertEqual(item.stock_status, InventoryItem.STATUS_LOW_STOCK)

    @override_settings(LOW_STOCK_THRESHOLD=10)
    def test_stock_status_available(self):
        item = InventoryItem.objects.create(name="Keyboard", quantity=25)
        self.assertEqual(item.stock_status, InventoryItem.STATUS_AVAILABLE)


class InventoryServiceUnitTests(TestCase):
    """Unit tests for service-layer business rules."""

    def setUp(self):
        self.admin_user = create_test_user(
            email="admininv@example.com", password="TestPass123!", role="ADMIN"
        )
        self.viewer_user = create_test_user(
            email="viewerinv@example.com", password="TestPass123!", role="STAFF"
        )
        # Assign a non-privileged role value to test write restrictions.
        self.viewer_user.role = "VIEWER"

    def test_create_inventory_item_rejects_non_admin(self):
        with self.assertRaises(PermissionDenied):
            create_inventory_item(
                user=self.viewer_user,
                name="Item",
                description="Desc",
                category="Cat",
                quantity=1,
            )

    def test_create_inventory_item_rejects_negative_quantity(self):
        with self.assertRaises(ValidationError):
            create_inventory_item(
                user=self.admin_user,
                name="Item",
                description="Desc",
                category="Cat",
                quantity=-1,
            )

    def test_update_inventory_item_rejects_invalid_field(self):
        item = create_inventory_item(
            user=self.admin_user,
            name="Item",
            description="Desc",
            category="Cat",
            quantity=5,
        )
        with self.assertRaises(ValidationError):
            update_inventory_item(self.admin_user, item, unknown_field="bad")

    def test_delete_inventory_item_removes_item(self):
        item = create_inventory_item(
            user=self.admin_user,
            name="ToDelete",
            description="Desc",
            category="Cat",
            quantity=3,
        )
        deleted = delete_inventory_item(self.admin_user, item)
        self.assertTrue(deleted)
        self.assertFalse(InventoryItem.objects.filter(id=item.id).exists())

    def test_search_inventory_items_matches_name_and_category(self):
        InventoryItem.objects.create(name="Dell Laptop", category="Hardware", quantity=1)
        InventoryItem.objects.create(name="Office Chair", category="Furniture", quantity=1)

        results = search_inventory_items("laptop")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, "Dell Laptop")


class InventorySignalsUnitTests(TestCase):
    """Unit tests for low-stock signal transitions."""

    @patch("inventory.signals.send_low_stock_alert_email")
    @override_settings(LOW_STOCK_THRESHOLD=10)
    def test_low_stock_alert_sent_on_transition(self, mocked_sender):
        # Create item above threshold, then update to low stock to trigger transition.
        item = InventoryItem.objects.create(name="Router", quantity=20, category="Network")
        mocked_sender.assert_not_called()

        item.quantity = 5
        item.save()

        mocked_sender.assert_called_once_with(item)


class InventoryCrudIntegrationTests(TestCase):
    """Integration tests for authenticated inventory CRUD operations."""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = create_test_user(
            email="crudadmin@example.com", password="CrudPass123!", role="ADMIN"
        )

    def _login_and_set_bearer_token(self):
        # Use real auth endpoint so CRUD tests run with JWT-authenticated requests.
        response = self.client.post(
            "/api/auth/login/",
            {"email": self.admin_user.email, "password": "CrudPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_inventory_crud_flow(self):
        self._login_and_set_bearer_token()

        # Create
        create_response = self.client.post(
            "/api/inventory/items/",
            {
                "name": "Monitor",
                "description": "27 inch display",
                "category": "Hardware",
                "quantity": 10,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        item_id = create_response.data["id"]

        # List
        list_response = self.client.get("/api/inventory/items/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(list_response.data), 1)

        # Partial update
        patch_response = self.client.patch(
            f"/api/inventory/items/{item_id}/",
            {"quantity": 4},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["quantity"], 4)

        # Delete
        delete_response = self.client.delete(f"/api/inventory/items/{item_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
