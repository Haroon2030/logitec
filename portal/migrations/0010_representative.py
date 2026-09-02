from django.db import migrations, models


def copy_legacy_rep_phone(apps, schema_editor):
    Representative = apps.get_model("portal", "Representative")
    WhatsAppConfig = apps.get_model("portal", "WhatsAppConfig")
    config = WhatsAppConfig.objects.filter(pk=1).first()
    if not config or not (config.phone_rep or "").strip():
        return
    phone = "".join(ch for ch in config.phone_rep if ch.isdigit())
    if phone.startswith("00"):
        phone = phone[2:]
    if not phone:
        return
    if Representative.objects.filter(phone=phone).exists():
        return
    Representative.objects.create(name="المندوب", phone=phone)


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0009_rep_reply"),
    ]

    operations = [
        migrations.CreateModel(
            name="Representative",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="اسم المندوب")),
                ("phone", models.CharField(max_length=40, verbose_name="رقم الجوال")),
            ],
            options={
                "verbose_name": "مندوب",
                "verbose_name_plural": "المندوبون",
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(copy_legacy_rep_phone, migrations.RunPython.noop),
    ]
