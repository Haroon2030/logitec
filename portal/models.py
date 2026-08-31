from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from .roles import ROLE_CHOICES, PURCHASING_MANAGER, normalize_role, role_label


class Supplier(models.Model):
    code = models.CharField("الرمز", max_length=32, unique=True)
    name = models.CharField("الاسم", max_length=200)
    initials = models.CharField("الاختصار", max_length=4, blank=True)
    contact_name = models.CharField("جهة الاتصال", max_length=120, blank=True)
    phone = models.CharField("الهاتف", max_length=40, blank=True)
    email = models.EmailField("البريد", blank=True)

    class Meta:
        verbose_name = "مورد"
        verbose_name_plural = "الموردون"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    code = models.CharField("رقم القسم", max_length=32, unique=True)
    name = models.CharField("اسم القسم", max_length=120)

    class Meta:
        verbose_name = "قسم"
        verbose_name_plural = "الأقسام"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Warehouse(models.Model):
    code = models.CharField("رقم المستودع", max_length=32, unique=True)
    name = models.CharField("اسم المستودع", max_length=120)
    city = models.CharField("المدينة", max_length=80, blank=True)
    capacity_percent = models.PositiveSmallIntegerField("نسبة الإشغال", default=0)

    class Meta:
        verbose_name = "مستودع"
        verbose_name_plural = "المستودعات"
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.city})"


class Product(models.Model):
    sku = models.CharField("رمز المنتج", max_length=40, unique=True)
    name = models.CharField("الاسم", max_length=200)
    unit_price = models.DecimalField("سعر الوحدة", max_digits=12, decimal_places=2)
    category = models.CharField("التصنيف", max_length=80, blank=True)

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SupplyRequest(models.Model):
    class Priority(models.TextChoices):
        HIGH = "high", "عالية"
        MEDIUM = "medium", "متوسطة"
        LOW = "low", "منخفضة"

    class Status(models.TextChoices):
        PENDING = "pending", "قيد الانتظار"
        APPROVED = "approved", "معتمد"
        SENT = "sent", "تم الإرسال"
        PREPARING = "preparing", "قيد التجهيز"
        IN_TRANSIT = "in_transit", "قيد النقل"
        RECEIVED = "received", "تم الاستلام"
        DELAYED = "delayed", "متأخر"

    number = models.CharField("رقم الطلب", max_length=32, unique=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="requests", verbose_name="المورد"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="purchase_requests",
        verbose_name="المستودع",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_requests",
        verbose_name="دائرة المشتريات",
    )
    sent_to_supplier_at = models.DateTimeField("أُرسل للمورد", null=True, blank=True)
    sent_to_warehouse_at = models.DateTimeField("أُرسل للمستودع", null=True, blank=True)
    priority = models.CharField(
        "الأولوية", max_length=16, choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(
        "الحالة", max_length=16, choices=Status.choices, default=Status.PENDING
    )
    destination = models.CharField("جهة الاستلام", max_length=200, blank=True)
    destination_address = models.CharField("العنوان", max_length=300, blank=True)
    zone = models.CharField("المنطقة", max_length=40, blank=True)
    aisle = models.CharField("الممر", max_length=40, blank=True)
    bin_code = models.CharField("الحاوية", max_length=40, blank=True)
    placed_at = models.DateTimeField("تاريخ الإنشاء", null=True, blank=True)
    shipped_at = models.DateTimeField("تاريخ الشحن", null=True, blank=True)
    eta = models.DateField("الوصول المتوقع", null=True, blank=True)
    attachment = models.FileField("الملف", upload_to="requests/", blank=True)
    created_at = models.DateTimeField("أُنشئ في", auto_now_add=True)

    class Meta:
        verbose_name = "طلب توريد"
        verbose_name_plural = "طلبات التوريد"
        ordering = ["-created_at"]

    def __str__(self):
        return self.number

    @property
    def attachment_name(self):
        if self.files.exists():
            return self.files.first().name
        if not self.attachment:
            return ""
        return self.attachment.name.rsplit("/", 1)[-1]

    @property
    def all_files(self):
        items = list(self.files.all())
        if items:
            return items
        if self.attachment:
            return [self]
        return []

    @property
    def file_count(self):
        count = self.files.count()
        if count:
            return count
        return 1 if self.attachment else 0

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def items_label(self):
        names = [item.product.name for item in self.items.all()[:2]]
        extra = self.items.count() - len(names)
        if extra > 0:
            return "، ".join(names) + f" +{extra}"
        return "، ".join(names) if names else "—"

    @property
    def tracking_steps(self):
        current = {
            "pending": 0,
            "approved": 0,
            "sent": 1,
            "preparing": 1,
            "in_transit": 2,
            "delayed": 2,
            "received": 4,
        }.get(self.status, 0)
        return current

    @property
    def grand_total(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0"))


class RequestFile(models.Model):
    request = models.ForeignKey(
        SupplyRequest, on_delete=models.CASCADE, related_name="files", verbose_name="الطلب"
    )
    file = models.FileField("الملف", upload_to="purchase_orders/")
    uploaded_at = models.DateTimeField("تاريخ الرفع", auto_now_add=True)

    class Meta:
        verbose_name = "ملف طلب توريد"
        verbose_name_plural = "ملفات طلب التوريد"
        ordering = ["uploaded_at"]

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self.file.name.rsplit("/", 1)[-1]


class RequestItem(models.Model):
    request = models.ForeignKey(
        SupplyRequest, on_delete=models.CASCADE, related_name="items", verbose_name="الطلب"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="request_items", verbose_name="المنتج"
    )
    quantity = models.PositiveIntegerField("الكمية")
    item_status = models.CharField("حالة العنصر", max_length=40, default="معبأ")

    class Meta:
        verbose_name = "عنصر طلب"
        verbose_name_plural = "عناصر الطلب"

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"

    @property
    def line_total(self):
        return self.product.unit_price * self.quantity


class Shipment(models.Model):
    class Status(models.TextChoices):
        UNSCHEDULED = "unscheduled", "غير مجدول"
        PENDING = "pending", "قيد الانتظار"
        CONFIRMED = "confirmed", "مؤكد"
        CONFLICT = "conflict", "تعارض"

    number = models.CharField("رقم الشحنة", max_length=32, unique=True)
    title = models.CharField("الوصف", max_length=200)
    pallets = models.PositiveIntegerField("عدد البليت")
    warehouse = models.ForeignKey(
        Warehouse,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="shipments",
        verbose_name="المستودع",
    )
    scheduled_date = models.DateField("تاريخ الجدولة", null=True, blank=True)
    scheduled_hour = models.PositiveSmallIntegerField("الساعة", null=True, blank=True)
    status = models.CharField(
        "الحالة", max_length=16, choices=Status.choices, default=Status.UNSCHEDULED
    )

    class Meta:
        verbose_name = "شحنة"
        verbose_name_plural = "الشحنات"
        ordering = ["scheduled_hour", "number"]

    def __str__(self):
        return self.number


class Alert(models.Model):
    class Level(models.TextChoices):
        CRITICAL = "critical", "حرج"
        SUCCESS = "success", "نجاح"
        INFO = "info", "معلومة"

    level = models.CharField("المستوى", max_length=16, choices=Level.choices)
    title = models.CharField("العنوان", max_length=200)
    detail = models.CharField("التفاصيل", max_length=300, blank=True)
    created_at = models.DateTimeField("أُنشئ في", auto_now_add=True)

    class Meta:
        verbose_name = "تنبيه"
        verbose_name_plural = "التنبيهات"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class InventoryItem(models.Model):
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="inventory", verbose_name="المستودع"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="inventory", verbose_name="المنتج"
    )
    quantity = models.PositiveIntegerField("الكمية", default=0)
    min_quantity = models.PositiveIntegerField("الحد الأدنى", default=0)

    class Meta:
        verbose_name = "صنف مخزون"
        verbose_name_plural = "المخزون"
        unique_together = ("warehouse", "product")

    def __str__(self):
        return f"{self.product} — {self.warehouse}"

    @property
    def is_low(self):
        return self.quantity <= self.min_quantity


class DailyVolume(models.Model):
    weekday = models.CharField("اليوم", max_length=16)
    volume = models.PositiveIntegerField("الحجم")
    highlight = models.BooleanField("تمييز", default=False)
    sort_order = models.PositiveSmallIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "حجم توريد يومي"
        verbose_name_plural = "أحجام التوريد اليومية"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.weekday}: {self.volume}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField("الهاتف", max_length=40, blank=True)
    role = models.CharField(
        "الدور",
        max_length=32,
        choices=ROLE_CHOICES,
        default=PURCHASING_MANAGER,
    )
    branch = models.CharField("الفرع", max_length=120, default="فرع دبي الرئيسي")
    timezone_name = models.CharField("المنطقة الزمنية", max_length=80, default="GST")
    language = models.CharField("اللغة", max_length=16, default="ar")
    photo = models.ImageField("الصورة", upload_to="profiles/", blank=True)

    class Meta:
        verbose_name = "ملف شخصي"
        verbose_name_plural = "الملفات الشخصية"

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def role_code(self):
        return normalize_role(self.user)

    @property
    def role_label_display(self):
        return role_label(self.user)


class WhatsAppConfig(models.Model):
    enabled = models.BooleanField("تفعيل الإشعارات", default=True)
    server_url = models.CharField("رابط سيرفر Evolution", max_length=255, blank=True)
    api_key = models.CharField("مفتاح API", max_length=255, blank=True)
    instance_name = models.CharField("اسم النسخة", max_length=80, blank=True)
    verify_ssl = models.BooleanField("التحقق من SSL", default=False)
    phone_rep = models.CharField("جوال المندوب", max_length=40, blank=True)
    phone_warehouse = models.CharField("جوال مسؤول المستودع", max_length=40, blank=True)
    phone_purchasing = models.CharField("جوال المشتريات", max_length=40, blank=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        verbose_name = "تهيئة واتساب"
        verbose_name_plural = "تهيئة واتساب"

    def __str__(self):
        return self.instance_name or "واتساب"

    @classmethod
    def load(cls):
        from django.conf import settings as dj_settings

        obj, _created = cls.objects.get_or_create(
            pk=1,
            defaults={
                "enabled": getattr(dj_settings, "EVOLUTION_NOTIFY_ENABLED", True),
                "server_url": getattr(dj_settings, "EVOLUTION_SERVER_URL", ""),
                "api_key": getattr(dj_settings, "EVOLUTION_API_KEY", ""),
                "instance_name": getattr(dj_settings, "EVOLUTION_INSTANCE_NAME", "farshops"),
                "verify_ssl": getattr(dj_settings, "EVOLUTION_VERIFY_SSL", False),
            },
        )
        dirty = []
        if not obj.server_url:
            obj.server_url = getattr(dj_settings, "EVOLUTION_SERVER_URL", "")
            dirty.append("server_url")
        if not obj.api_key:
            obj.api_key = getattr(dj_settings, "EVOLUTION_API_KEY", "")
            dirty.append("api_key")
        if not obj.instance_name:
            obj.instance_name = getattr(dj_settings, "EVOLUTION_INSTANCE_NAME", "farshops")
            dirty.append("instance_name")
        if dirty:
            obj.save(update_fields=dirty)
        return obj
