from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        # Drop the old FK column (was stored as created_by_id in the DB).
        migrations.RemoveField(
            model_name="inventoryitem",
            name="created_by",
        ),
        # Add a plain EmailField column named created_by.
        migrations.AddField(
            model_name="inventoryitem",
            name="created_by",
            field=models.EmailField(
                blank=True,
                help_text="Email of the user who created this inventory item.",
                max_length=254,
                null=True,
            ),
        ),
        # Rename the table from inventory_inventoryitem to inventory_items.
        migrations.AlterModelTable(
            name="inventoryitem",
            table="inventory_items",
        ),
    ]
