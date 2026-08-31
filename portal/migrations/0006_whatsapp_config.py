from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0005_user_roles"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsAppConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=True, verbose_name="تفعيل الإشعارات")),
                ("server_url", models.CharField(blank=True, max_length=255, verbose_name="رابط سيرفر Evolution")),
                ("api_key", models.CharField(blank=True, max_length=255, verbose_name="مفتاح API")),
                ("instance_name", models.CharField(blank=True, max_length=80, verbose_name="اسم النسخة")),
                ("verify_ssl", models.BooleanField(default=False, verbose_name="التحقق من SSL")),
                ("phone_rep", models.CharField(blank=True, max_length=40, verbose_name="جوال المندوب")),
                ("phone_warehouse", models.CharField(blank=True, max_length=40, verbose_name="جوال مسؤول المستودع")),
                ("phone_purchasing", models.CharField(blank=True, max_length=40, verbose_name="جوال المشتريات")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")),
            ],
            options={
                "verbose_name": "تهيئة واتساب",
                "verbose_name_plural": "تهيئة واتساب",
            },
        ),
    ]
