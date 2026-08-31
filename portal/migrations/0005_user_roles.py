from django.db import migrations, models


ROLE_ALIASES = {
    "موظف شراء": "purchasing_staff",
    "موظف مشتريات": "purchasing_staff",
    "purchasing_staff": "purchasing_staff",
    "موظف مستودع": "warehouse_staff",
    "warehouse_staff": "warehouse_staff",
    "مدير مشتريات": "purchasing_manager",
    "purchasing_manager": "purchasing_manager",
    "سوبر ادمن": "super_admin",
    "super_admin": "super_admin",
    "superadmin": "super_admin",
    "admin": "super_admin",
}

KNOWN = {
    "purchasing_staff",
    "warehouse_staff",
    "purchasing_manager",
    "super_admin",
}


def convert_roles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("portal", "UserProfile")
    for profile in UserProfile.objects.select_related("user"):
        raw = profile.role or ""
        code = raw if raw in KNOWN else ROLE_ALIASES.get(raw, "purchasing_manager")
        if getattr(profile.user, "is_superuser", False):
            code = "super_admin"
        if profile.role != code:
            profile.role = code
            profile.save(update_fields=["role"])
    for user in User.objects.filter(is_superuser=True):
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"role": "super_admin"},
        )
        if not created and profile.role != "super_admin":
            profile.role = "super_admin"
            profile.save(update_fields=["role"])


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0004_setup_departments"),
    ]

    operations = [
        migrations.RunPython(convert_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userprofile",
            name="role",
            field=models.CharField(
                choices=[
                    ("purchasing_staff", "موظف شراء"),
                    ("warehouse_staff", "موظف مستودع"),
                    ("purchasing_manager", "مدير مشتريات"),
                    ("super_admin", "سوبر ادمن"),
                ],
                default="purchasing_manager",
                max_length=32,
                verbose_name="الدور",
            ),
        ),
    ]
