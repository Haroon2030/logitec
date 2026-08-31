from django.core.management.base import BaseCommand

from portal.role_accounts import ensure_demo_accounts, normalize_existing_roles


class Command(BaseCommand):
    help = "يوحّد أدوار المستخدمين وينشئ حسابات الأدوار التجريبية إن لم توجد"

    def handle(self, *args, **options):
        normalize_existing_roles()
        created = ensure_demo_accounts(reset_password=False)
        self.stdout.write(self.style.SUCCESS("تم توحيد أدوار المستخدمين"))
        if created:
            self.stdout.write("حسابات جديدة: " + ", ".join(created))
        else:
            self.stdout.write("لا توجد حسابات جديدة")
