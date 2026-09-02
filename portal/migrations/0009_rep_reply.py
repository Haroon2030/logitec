import uuid

from django.db import migrations, models


def fill_reply_tokens(apps, schema_editor):
    SupplyRequest = apps.get_model("portal", "SupplyRequest")
    for row in SupplyRequest.objects.all():
        if not row.reply_token:
            row.reply_token = uuid.uuid4()
            row.save(update_fields=["reply_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0008_arabic_labels"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplyrequest",
            name="reply_token",
            field=models.UUIDField(
                editable=False,
                null=True,
                verbose_name="رمز رد المندوب",
            ),
        ),
        migrations.AddField(
            model_name="supplyrequest",
            name="rep_replied_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="رد المندوب في"),
        ),
        migrations.RunPython(fill_reply_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="supplyrequest",
            name="reply_token",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="رمز رد المندوب",
            ),
        ),
    ]
