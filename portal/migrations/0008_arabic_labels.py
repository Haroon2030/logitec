from django.db import migrations


SUPPLIER_NAMES = {
    "GlobalTech Supplies": "الإمدادات التقنية العالمية",
    "Apex Raw Materials": "أبيكس للمواد الخام",
    "Nexus Packaging Solutions": "نكسس لحلول التغليف",
    "TechSupply Global Ltd": "التوريدات التقنية العالمية",
    "Metro Industrial Parts": "مترو للقطع الصناعية",
}

REQUEST_NUMBERS = {
    "REQ-2024-089": "توريد-2024-089",
    "REQ-2024-088": "توريد-2024-088",
    "REQ-2024-087": "توريد-2024-087",
    "REQ-2024-086": "توريد-2024-086",
    "REQ-2024-085": "توريد-2024-085",
    "REQ-2024-084": "توريد-2024-084",
    "REQ-2024-083": "توريد-2024-083",
    "REQ-2024-082": "توريد-2024-082",
    "ORD-2023-8942": "توريد-2023-8942",
}


def arabic_labels(apps, schema_editor):
    Supplier = apps.get_model("portal", "Supplier")
    SupplyRequest = apps.get_model("portal", "SupplyRequest")
    for english, arabic in SUPPLIER_NAMES.items():
        Supplier.objects.filter(name=english).update(name=arabic)
    for old, new in REQUEST_NUMBERS.items():
        if SupplyRequest.objects.filter(number=new).exists():
            continue
        SupplyRequest.objects.filter(number=old).update(number=new)
    for obj in SupplyRequest.objects.filter(number__startswith="PO-"):
        candidate = "توريد-" + obj.number[3:]
        if not SupplyRequest.objects.filter(number=candidate).exists():
            obj.number = candidate
            obj.save(update_fields=["number"])
    for obj in SupplyRequest.objects.filter(number__startswith="REQ-"):
        candidate = obj.number.replace("REQ-", "توريد-", 1)
        if not SupplyRequest.objects.filter(number=candidate).exists():
            obj.number = candidate
            obj.save(update_fields=["number"])
    for obj in SupplyRequest.objects.filter(number__startswith="ORD-"):
        candidate = obj.number.replace("ORD-", "توريد-", 1)
        if not SupplyRequest.objects.filter(number=candidate).exists():
            obj.number = candidate
            obj.save(update_fields=["number"])


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0007_supply_schedule"),
    ]

    operations = [
        migrations.RunPython(arabic_labels, noop),
    ]
