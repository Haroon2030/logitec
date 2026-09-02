from django.db import migrations, models


def copy_legacy_warehouse_phone(apps, schema_editor):
    WarehouseKeeper = apps.get_model("portal", "WarehouseKeeper")
    Warehouse = apps.get_model("portal", "Warehouse")
    WhatsAppConfig = apps.get_model("portal", "WhatsAppConfig")
    config = WhatsAppConfig.objects.filter(pk=1).first()
    if not config or not (config.phone_warehouse or "").strip():
        return
    phone = "".join(ch for ch in config.phone_warehouse if ch.isdigit())
    if phone.startswith("00"):
        phone = phone[2:]
    if not phone or WarehouseKeeper.objects.filter(phone=phone).exists():
        return
    keeper = WarehouseKeeper.objects.create(name="أمين المستودع", phone=phone)
    warehouses = list(Warehouse.objects.all())
    if warehouses:
        keeper.warehouses.set(warehouses)


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0010_representative"),
    ]

    operations = [
        migrations.CreateModel(
            name="WarehouseKeeper",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="اسم الأمين")),
                ("phone", models.CharField(max_length=40, verbose_name="رقم الجوال")),
                (
                    "warehouses",
                    models.ManyToManyField(
                        related_name="keepers",
                        to="portal.warehouse",
                        verbose_name="المستودعات",
                    ),
                ),
            ],
            options={
                "verbose_name": "أمين مستودع",
                "verbose_name_plural": "أمناء المستودعات",
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(copy_legacy_warehouse_phone, migrations.RunPython.noop),
    ]
