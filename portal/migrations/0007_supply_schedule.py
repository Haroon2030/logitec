from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0006_whatsapp_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplyrequest",
            name="scheduled_date",
            field=models.DateField(blank=True, null=True, verbose_name="تاريخ الاستلام المجدول"),
        ),
        migrations.AddField(
            model_name="supplyrequest",
            name="scheduled_hour",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="ساعة الاستلام"),
        ),
    ]
