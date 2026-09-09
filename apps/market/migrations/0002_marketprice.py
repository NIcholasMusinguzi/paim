from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("market", "0001_initial")]

    operations = [migrations.CreateModel(
        name="MarketPrice",
        fields=[
            ("id", models.BigAutoField(auto_created=True,
             primary_key=True, serialize=False, verbose_name="ID")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("item_name", models.CharField(max_length=120)),
            ("category", models.CharField(choices=[
             ("produce", "Produce"), ("input", "Farm input")], max_length=12)),
            ("price", models.PositiveIntegerField()),
            ("unit", models.CharField(max_length=32)),
            ("market", models.CharField(blank=True, max_length=120)),
            ("price_date", models.DateField()),
            ("source", models.CharField(blank=True, max_length=120)),
        ],
        options={
            "ordering": ["-price_date", "category", "item_name"],
            "indexes": [models.Index(fields=["price_date", "category"], name="market_mark_price_d_94f277_idx")],
        },
    )]
