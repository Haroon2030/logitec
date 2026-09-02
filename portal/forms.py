from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User

from .models import Department, Representative, Supplier, SupplyRequest, UserProfile, Warehouse, WarehouseKeeper, WhatsAppConfig
from .roles import ROLE_ALIASES, ROLE_CHOICES, ROLE_LABELS, PURCHASING_STAFF, SUPER_ADMIN


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            return []
        items = data if isinstance(data, (list, tuple)) else [data]
        return [super().clean(item, initial) for item in items if item]


class StyledAuthForm(AuthenticationForm):
    username = forms.CharField(
        label="رقم المستخدم",
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "أدخل رقم المستخدم",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="كلمة المرور",
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        ),
    )


class SupplyRequestForm(forms.ModelForm):
    files = MultipleFileField(
        label="ملفات طلب التوريد",
        required=False,
        widget=MultipleFileInput(
            attrs={
                "class": "field-input file-input",
                "accept": ".pdf,.xls,.xlsx,.csv,.doc,.docx,.png,.jpg,.jpeg",
            }
        ),
    )

    class Meta:
        model = SupplyRequest
        fields = ("supplier", "warehouse", "priority")
        widgets = {
            "supplier": forms.Select(attrs={"class": "field-input"}),
            "warehouse": forms.Select(attrs={"class": "field-input"}),
            "priority": forms.Select(attrs={"class": "field-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.all()
        self.fields["supplier"].empty_label = "اختر المورد"
        self.fields["warehouse"].queryset = Warehouse.objects.all()
        self.fields["warehouse"].empty_label = "اختر المستودع"
        self.fields["warehouse"].required = True

    def clean(self):
        cleaned = super().clean()
        uploaded = cleaned.get("files") or []
        if not uploaded:
            self.add_error("files", "ارفع ملف طلب توريد واحداً على الأقل")
        cleaned["uploaded_files"] = uploaded
        return cleaned


ARRIVAL_HOUR_CHOICES = [(hour, f"{hour:02d}:00") for hour in range(6, 23)]


class ISODateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")
        super().__init__(*args, **kwargs)


class RepArrivalForm(forms.Form):
    arrival_date = forms.DateField(
        label="تاريخ التوريد",
        localize=False,
        input_formats=["%Y-%m-%d"],
        widget=ISODateInput(attrs={"class": "field-input"}),
    )
    arrival_hour = forms.TypedChoiceField(
        label="ساعة الوصول",
        coerce=int,
        choices=ARRIVAL_HOUR_CHOICES,
        widget=forms.Select(attrs={"class": "field-input"}),
    )


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label="الاسم الأول",
        widget=forms.TextInput(attrs={"class": "field-input"}),
    )
    last_name = forms.CharField(
        label="اسم العائلة",
        widget=forms.TextInput(attrs={"class": "field-input"}),
    )

    class Meta:
        model = UserProfile
        fields = ("timezone_name", "language")
        widgets = {
            "timezone_name": forms.Select(
                choices=[
                    ("GST", "GST (توقيت الخليج القياسي)"),
                    ("AST", "AST (توقيت السعودية)"),
                    ("UTC", "UTC"),
                ],
                attrs={"class": "field-input"},
            ),
            "language": forms.Select(
                choices=[("ar", "العربية"), ("en", "English")],
                attrs={"class": "field-input"},
            ),
        }

    def __init__(self, *args, **kwargs):
        user: User = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name

    def save(self, user: User, commit=True):
        profile = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            profile.save()
        return profile


class PortalUserForm(forms.Form):
    username = forms.CharField(
        label="رقم المستخدم",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "field-input", "placeholder": "مثال: 1"}),
    )
    full_name = forms.CharField(
        label="الاسم",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "field-input", "placeholder": "اسم الموظف"}),
    )
    phone = forms.CharField(
        label="رقم الجوال",
        max_length=40,
        widget=forms.TextInput(
            attrs={"class": "field-input", "placeholder": "9665xxxxxxxx", "dir": "ltr"}
        ),
    )
    role = forms.ChoiceField(
        label="الدور",
        choices=ROLE_CHOICES,
        initial=PURCHASING_STAFF,
        widget=forms.Select(attrs={"class": "field-input"}),
    )
    password = forms.CharField(
        label="كلمة المرور",
        min_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={"class": "field-input", "placeholder": "••••••", "autocomplete": "new-password"}),
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance:
            self.fields["password"].required = False
            try:
                profile = instance.profile
            except UserProfile.DoesNotExist:
                profile = None
            self.fields["username"].initial = instance.username
            self.fields["full_name"].initial = instance.get_full_name() or instance.username
            if instance.is_superuser:
                self.fields["role"].initial = SUPER_ADMIN
            elif profile:
                raw = profile.role or ""
                self.fields["role"].initial = ROLE_ALIASES.get(
                    raw, raw if raw in ROLE_LABELS else PURCHASING_STAFF
                )
            if profile:
                self.fields["phone"].initial = profile.phone
        else:
            self.fields["password"].required = True

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        qs = User.objects.filter(username=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("رقم المستخدم موجود مسبقاً")
        return username

    def clean_phone(self):
        from .whatsapp import normalize_phone

        phone = normalize_phone(self.cleaned_data.get("phone"))
        if not phone:
            raise forms.ValidationError("أدخل رقم جوال صحيح")
        return phone

    def clean_password(self):
        password = self.cleaned_data.get("password") or ""
        if not self.instance and len(password) < 4:
            raise forms.ValidationError("أدخل كلمة مرور من 4 أحرف على الأقل")
        if password and len(password) < 4:
            raise forms.ValidationError("أدخل كلمة مرور من 4 أحرف على الأقل")
        return password

    def apply_name(self, user):
        full_name = self.cleaned_data["full_name"].strip()
        parts = full_name.split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
        return user


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("code", "name")
        labels = {"code": "رقم القسم", "name": "اسم القسم"}
        widgets = {
            "code": forms.TextInput(attrs={"class": "field-input", "placeholder": "مثال: DEP-01"}),
            "name": forms.TextInput(attrs={"class": "field-input", "placeholder": "اسم القسم"}),
        }


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ("code", "name")
        labels = {"code": "رقم المستودع", "name": "اسم المستودع"}
        widgets = {
            "code": forms.TextInput(attrs={"class": "field-input", "placeholder": "مثال: WH-01"}),
            "name": forms.TextInput(attrs={"class": "field-input", "placeholder": "اسم المستودع"}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ("code", "name")
        labels = {"code": "رقم المورد", "name": "اسم المورد"}
        widgets = {
            "code": forms.TextInput(attrs={"class": "field-input", "placeholder": "مثال: SUP-100"}),
            "name": forms.TextInput(attrs={"class": "field-input", "placeholder": "اسم المورد"}),
        }


class RepresentativeForm(forms.ModelForm):
    class Meta:
        model = Representative
        fields = ("name", "phone")
        widgets = {
            "name": forms.TextInput(attrs={"class": "field-input", "placeholder": "اسم المندوب"}),
            "phone": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "9665xxxxxxxx", "dir": "ltr"}
            ),
        }

    def clean_phone(self):
        from .whatsapp import normalize_phone

        phone = normalize_phone(self.cleaned_data.get("phone"))
        if not phone:
            raise forms.ValidationError("أدخل رقم جوال صحيح")
        qs = Representative.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("رقم الجوال مسجّل لمندوب آخر")
        return phone


class WarehouseKeeperForm(forms.ModelForm):
    class Meta:
        model = WarehouseKeeper
        fields = ("name", "phone", "warehouses")
        widgets = {
            "name": forms.TextInput(attrs={"class": "field-input", "placeholder": "اسم أمين المستودع"}),
            "phone": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "9665xxxxxxxx", "dir": "ltr"}
            ),
            "warehouses": forms.CheckboxSelectMultiple(attrs={"class": "check-list"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["warehouses"].queryset = Warehouse.objects.all().order_by("name")
        self.fields["warehouses"].required = True
        self.fields["warehouses"].label = "المستودعات المرتبطة"

    def clean_phone(self):
        from .whatsapp import normalize_phone

        phone = normalize_phone(self.cleaned_data.get("phone"))
        if not phone:
            raise forms.ValidationError("أدخل رقم جوال صحيح")
        qs = WarehouseKeeper.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("رقم الجوال مسجّل لأمين آخر")
        return phone

    def clean_warehouses(self):
        warehouses = self.cleaned_data.get("warehouses")
        if not warehouses:
            raise forms.ValidationError("اختر مستودعاً واحداً على الأقل")
        return warehouses


class WhatsAppConfigForm(forms.ModelForm):
    class Meta:
        model = WhatsAppConfig
        fields = (
            "enabled",
            "server_url",
            "api_key",
            "instance_name",
            "verify_ssl",
        )
        widgets = {
            "enabled": forms.CheckboxInput(attrs={"class": "check-input"}),
            "server_url": forms.URLInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "http://72.61.107.230:8081",
                    "dir": "ltr",
                }
            ),
            "api_key": forms.TextInput(attrs={"class": "field-input", "dir": "ltr"}),
            "instance_name": forms.TextInput(attrs={"class": "field-input", "dir": "ltr"}),
            "verify_ssl": forms.CheckboxInput(attrs={"class": "check-input"}),
        }

    def __init__(self, *args, is_super_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_super_admin:
            for name in ("server_url", "api_key", "instance_name", "verify_ssl"):
                self.fields.pop(name, None)


class PortalPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "old_password": "كلمة المرور الحالية",
            "new_password1": "كلمة المرور الجديدة",
            "new_password2": "تأكيد كلمة المرور",
        }
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "field-input"
            field.label = labels.get(name, field.label)
