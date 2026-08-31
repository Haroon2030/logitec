from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import (
    Alert,
    DailyVolume,
    Department,
    InventoryItem,
    Product,
    RequestFile,
    RequestItem,
    Shipment,
    Supplier,
    SupplyRequest,
    Warehouse,
)
from portal.role_accounts import ensure_demo_accounts


class Command(BaseCommand):
    help = "يملأ المنصة ببيانات تجريبية مطابقة للتصميم"

    def handle(self, *args, **options):
        self.stdout.write("جاري تجهيز البيانات التجريبية...")
        ensure_demo_accounts(reset_password=False)
        user = User.objects.get(username="1")

        suppliers = {
            "globaltech": Supplier.objects.update_or_create(
                code="SUP-GT-01",
                defaults={
                    "name": "الإمدادات التقنية العالمية",
                    "initials": "GT",
                    "contact_name": "ليلى حسن",
                    "phone": "+971 4 200 1100",
                    "email": "ops@globaltech.supplies",
                },
            )[0],
            "apex": Supplier.objects.update_or_create(
                code="SUP-APX-02",
                defaults={
                    "name": "أبيكس للمواد الخام",
                    "initials": "AX",
                    "contact_name": "عمر الراشد",
                    "phone": "+966 11 440 2200",
                    "email": "sales@apexraw.com",
                },
            )[0],
            "nexus": Supplier.objects.update_or_create(
                code="SUP-NX-03",
                defaults={
                    "name": "نكسس لحلول التغليف",
                    "initials": "NX",
                    "contact_name": "هند العلي",
                    "phone": "+971 2 333 4400",
                    "email": "hello@nexuspack.ae",
                },
            )[0],
            "techsupply": Supplier.objects.update_or_create(
                code="SUP-992-HK",
                defaults={
                    "name": "التوريدات التقنية العالمية",
                    "initials": "TS",
                    "contact_name": "سارة تشن",
                    "phone": "+852 2849 5555",
                    "email": "schen@techsupply.global",
                },
            )[0],
            "metro": Supplier.objects.update_or_create(
                code="SUP-MT-05",
                defaults={
                    "name": "مترو للقطع الصناعية",
                    "initials": "MI",
                    "contact_name": "خالد فهد",
                    "phone": "+966 12 880 3000",
                    "email": "parts@metroind.sa",
                },
            )[0],
        }

        warehouses = {
            "a": Warehouse.objects.update_or_create(
                code="أ",
                defaults={"name": "المستودع أ", "city": "الرياض", "capacity_percent": 80},
            )[0],
            "b": Warehouse.objects.update_or_create(
                code="ب",
                defaults={"name": "المستودع ب", "city": "جدة", "capacity_percent": 45},
            )[0],
            "c": Warehouse.objects.update_or_create(
                code="ج",
                defaults={"name": "المستودع ج", "city": "الدمام", "capacity_percent": 92},
            )[0],
        }

        for code, name in [
            ("DEP-01", "المشتريات"),
            ("DEP-02", "المستودعات"),
            ("DEP-03", "المالية"),
        ]:
            Department.objects.update_or_create(code=code, defaults={"name": name})

        products = {
            "ram": Product.objects.update_or_create(
                sku="RAM-16-DDR5",
                defaults={"name": "وحدات ذاكرة RAM", "unit_price": Decimal("85.00"), "category": "إلكترونيات"},
            )[0],
            "gasket": Product.objects.update_or_create(
                sku="GSK-HT-40",
                defaults={"name": "حشوات حرارية", "unit_price": Decimal("12.50"), "category": "قطع غيار"},
            )[0],
            "pcb": Product.objects.update_or_create(
                sku="PCB-10K",
                defaults={"name": "لوحات دوائر مطبوعة", "unit_price": Decimal("4.20"), "category": "إلكترونيات"},
            )[0],
            "alu": Product.objects.update_or_create(
                sku="ALU-5T",
                defaults={"name": "ألمنيوم خام", "unit_price": Decimal("2100.00"), "category": "مواد خام"},
            )[0],
            "ctrl": Product.objects.update_or_create(
                sku="IC-90-X22",
                defaults={"name": "أجهزة تحكم صناعية X-90", "unit_price": Decimal("240.00"), "category": "أتمتة"},
            )[0],
            "servo": Product.objects.update_or_create(
                sku="RA-SV2-44",
                defaults={"name": "محركات ذراع روبوتية v2", "unit_price": Decimal("850.00"), "category": "أتمتة"},
            )[0],
            "cable": Product.objects.update_or_create(
                sku="CBL-HD-100",
                defaults={"name": "كابلات حساسات ثقيلة (100م)", "unit_price": Decimal("120.00"), "category": "كهرباء"},
            )[0],
            "pack": Product.objects.update_or_create(
                sku="PKG-STD",
                defaults={"name": "مواد تغليف", "unit_price": Decimal("18.00"), "category": "تغليف"},
            )[0],
            "auto": Product.objects.update_or_create(
                sku="AUTO-SP-08",
                defaults={"name": "قطع غيار سيارات", "unit_price": Decimal("64.00"), "category": "سيارات"},
            )[0],
            "med": Product.objects.update_or_create(
                sku="MED-12P",
                defaults={"name": "مواد طبية", "unit_price": Decimal("95.00"), "category": "طبي"},
            )[0],
        }

        RequestItem.objects.all().delete()
        RequestFile.objects.all().delete()
        SupplyRequest.objects.all().delete()

        tz = timezone.get_current_timezone()
        requests_data = [
            {
                "number": "توريد-2024-089",
                "supplier": suppliers["globaltech"],
                "priority": SupplyRequest.Priority.HIGH,
                "status": SupplyRequest.Status.APPROVED,
                "items": [(products["ram"], 1250)],
                "eta": date(2023, 10, 16),
            },
            {
                "number": "توريد-2024-088",
                "supplier": suppliers["metro"],
                "priority": SupplyRequest.Priority.MEDIUM,
                "status": SupplyRequest.Status.PENDING,
                "items": [(products["gasket"], 400)],
                "eta": date(2023, 10, 18),
            },
            {
                "number": "توريد-2024-087",
                "supplier": suppliers["nexus"],
                "priority": SupplyRequest.Priority.LOW,
                "status": SupplyRequest.Status.SENT,
                "items": [(products["pack"], 220)],
                "eta": date(2023, 10, 15),
            },
            {
                "number": "توريد-2024-086",
                "supplier": suppliers["apex"],
                "priority": SupplyRequest.Priority.HIGH,
                "status": SupplyRequest.Status.PENDING,
                "items": [(products["alu"], 5)],
                "eta": date(2023, 10, 14),
            },
            {
                "number": "توريد-2023-8942",
                "supplier": suppliers["techsupply"],
                "priority": SupplyRequest.Priority.HIGH,
                "status": SupplyRequest.Status.IN_TRANSIT,
                "items": [
                    (products["ctrl"], 150),
                    (products["servo"], 45),
                    (products["cable"], 20),
                ],
                "destination": "مركز دبي اللوجستي المركزي",
                "destination_address": "المنطقة الحرة جبل علي، دبي، الإمارات",
                "zone": "المنطقة ب",
                "aisle": "الممر 14",
                "bin_code": "الحاوية 42-C",
                "placed_at": timezone.make_aware(datetime(2023, 10, 12, 9, 41), tz),
                "shipped_at": timezone.make_aware(datetime(2023, 10, 13, 14, 20), tz),
                "eta": date(2023, 10, 16),
            },
            {
                "number": "توريد-2024-085",
                "supplier": suppliers["globaltech"],
                "priority": SupplyRequest.Priority.MEDIUM,
                "status": SupplyRequest.Status.IN_TRANSIT,
                "items": [(products["pcb"], 10000)],
                "eta": date(2023, 10, 16),
            },
            {
                "number": "توريد-2024-084",
                "supplier": suppliers["apex"],
                "priority": SupplyRequest.Priority.HIGH,
                "status": SupplyRequest.Status.DELAYED,
                "items": [(products["alu"], 5)],
                "eta": date(2023, 10, 10),
            },
            {
                "number": "توريد-2024-083",
                "supplier": suppliers["nexus"],
                "priority": SupplyRequest.Priority.LOW,
                "status": SupplyRequest.Status.RECEIVED,
                "items": [(products["pack"], 800)],
                "eta": date(2023, 10, 12),
            },
            {
                "number": "توريد-2024-082",
                "supplier": suppliers["metro"],
                "priority": SupplyRequest.Priority.MEDIUM,
                "status": SupplyRequest.Status.PREPARING,
                "items": [(products["auto"], 320)],
                "eta": date(2023, 10, 18),
            },
        ]

        warehouse_cycle = [warehouses["a"], warehouses["b"], warehouses["c"]]
        now = timezone.now()
        for index, data in enumerate(requests_data):
            items = data.pop("items")
            data["warehouse"] = warehouse_cycle[index % 3]
            data["created_by"] = user
            if data["status"] != SupplyRequest.Status.PENDING:
                sent_at = data.get("placed_at") or now
                data.setdefault("sent_to_supplier_at", sent_at)
                data.setdefault("sent_to_warehouse_at", sent_at)
            obj = SupplyRequest.objects.create(**data)
            for product, qty in items:
                RequestItem.objects.create(request=obj, product=product, quantity=qty, item_status="معبأ")

        Shipment.objects.all().delete()
        Shipment.objects.create(
            number="DEL-1029",
            title="قطع غيار سيارات",
            pallets=8,
            status=Shipment.Status.UNSCHEDULED,
        )
        Shipment.objects.create(
            number="DEL-4450",
            title="مواد تغليف",
            pallets=2,
            status=Shipment.Status.UNSCHEDULED,
        )
        Shipment.objects.create(
            number="DEL-9921",
            title="إلكترونيات",
            pallets=4,
            warehouse=warehouses["a"],
            scheduled_date=date(2023, 10, 24),
            scheduled_hour=8,
            status=Shipment.Status.CONFIRMED,
        )
        Shipment.objects.create(
            number="DEL-8834",
            title="مواد طبية",
            pallets=12,
            warehouse=warehouses["b"],
            scheduled_date=date(2023, 10, 24),
            scheduled_hour=9,
            status=Shipment.Status.PENDING,
        )
        Shipment.objects.create(
            number="DEL-1102",
            title="شحنة متعارضة",
            pallets=6,
            warehouse=warehouses["c"],
            scheduled_date=date(2023, 10, 24),
            scheduled_hour=10,
            status=Shipment.Status.CONFLICT,
        )

        Alert.objects.all().delete()
        Alert.objects.create(
            level=Alert.Level.CRITICAL,
            title="تأخر أمر توريد",
            detail="أُرسل للمورد والمستودع وما زال بانتظار الاستلام",
        )
        Alert.objects.create(
            level=Alert.Level.SUCCESS,
            title="تم استلام أمر توريد",
            detail="المستودع أكّد استلام ملفات التوريد",
        )
        Alert.objects.create(
            level=Alert.Level.INFO,
            title="أمر توريد بانتظار الاستلام",
            detail="الملفات وُجّهت إلى المورد والمستودع",
        )

        DailyVolume.objects.all().delete()
        for order, (day, volume, highlight) in enumerate(
            [
                ("السبت", 420, False),
                ("الأحد", 610, False),
                ("الاثنين", 540, False),
                ("الثلاثاء", 880, True),
                ("الأربعاء", 500, False),
                ("الخميس", 730, False),
                ("الجمعة", 310, False),
            ]
        ):
            DailyVolume.objects.create(weekday=day, volume=volume, highlight=highlight, sort_order=order)

        InventoryItem.objects.all().delete()
        stock = [
            (warehouses["a"], products["ram"], 180, 400),
            (warehouses["a"], products["pcb"], 4200, 2000),
            (warehouses["a"], products["ctrl"], 64, 40),
            (warehouses["b"], products["pack"], 960, 200),
            (warehouses["b"], products["med"], 140, 80),
            (warehouses["b"], products["gasket"], 70, 120),
            (warehouses["c"], products["alu"], 18, 10),
            (warehouses["c"], products["auto"], 210, 90),
            (warehouses["c"], products["servo"], 22, 15),
            (warehouses["c"], products["cable"], 48, 30),
        ]
        for warehouse, product, qty, minimum in stock:
            InventoryItem.objects.create(
                warehouse=warehouse, product=product, quantity=qty, min_quantity=minimum
            )

        self.stdout.write(self.style.SUCCESS("تم تجهيز البيانات بنجاح."))
        self.stdout.write("المستخدم: 1")
        self.stdout.write("كلمة المرور: 526400")
