from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User

from .models import Department, Supplier, SupplyRequest, UserProfile, Warehouse, WhatsAppConfig
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


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label="الاسم الأول",
        widget=forms.TextInput(attrs={"class": "field-input"}),
    )
    last_name = forms.CharField(
        label="اسم العائلة",
        widget=forms.TextInput(attrs={"class": "field-input"}),
    )
    email = forms.EmailField(
        label="البريد الإلكتروني",
        disabled=True,
        required=False,
        widget=forms.EmailInput(attrs={"class": "field-input", "readonly": True}),
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
        self.fields["email"].initial = user.email

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
    password = forms.CharField(
        label="كلمة المرور",
        min_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={"class": "field-input", "placeholder": "••••••", "autocomplete": "new-password"}),
    )
    role = forms.ChoiceField(
        label="الدور / الصلاحية",
        choices=ROLE_CHOICES,
        initial=PURCHASING_STAFF,
        widget=forms.Select(attrs={"class": "field-input"}),
    )
    email = forms.EmailField(
        label="البريد",
        required=False,
        widget=forms.EmailInput(attrs={"class": "field-input"}),
    )
    phone = forms.CharField(
        label="الهاتف",
        required=False,
        max_length=40,
        widget=forms.TextInput(attrs={"class": "field-input"}),
    )
    branch = forms.CharField(
        label="الفرع",
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={"class": "field-input"}),
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
            self.fields["email"].initial = instance.email
            if instance.is_superuser:
                self.fields["role"].initial = SUPER_ADMIN
            elif profile:
                raw = profile.role or ""
                self.fields["role"].initial = ROLE_ALIASES.get(
                    raw, raw if raw in ROLE_LABELS else PURCHASING_STAFF
                )
            if profile:
                self.fields["phone"].initial = profile.phone
                self.fields["branch"].initial = profile.branch
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


class WhatsAppConfigForm(forms.ModelForm):
    class Meta:
        model = WhatsAppConfig
        fields = (
            "enabled",
            "server_url",
            "api_key",
            "instance_name",
            "verify_ssl",
            "phone_rep",
            "phone_warehouse",
            "phone_purchasing",
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
            "phone_rep": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "9665xxxxxxxx", "dir": "ltr"}
            ),
            "phone_warehouse": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "9665xxxxxxxx", "dir": "ltr"}
            ),
            "phone_purchasing": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "9665xxxxxxxx", "dir": "ltr"}
            ),
        }


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
