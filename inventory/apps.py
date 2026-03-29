from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"

    def ready(self):
        # Ensure signal handlers are connected when the app is ready
        import inventory.signals  # noqa: F401
