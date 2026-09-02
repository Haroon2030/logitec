from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

PURCHASING_STAFF = "purchasing_staff"
WAREHOUSE_STAFF = "warehouse_staff"
PURCHASING_MANAGER = "purchasing_manager"
SUPER_ADMIN = "super_admin"

ROLE_LABELS = {
    PURCHASING_STAFF: "موظف شراء",
    WAREHOUSE_STAFF: "موظف مستودع",
    PURCHASING_MANAGER: "مدير مشتريات",
    SUPER_ADMIN: "سوبر ادمن",
}

ROLE_CHOICES = [(key, label) for key, label in ROLE_LABELS.items()]

ROLE_ALIASES = {
    "موظف شراء": PURCHASING_STAFF,
    "موظف مشتريات": PURCHASING_STAFF,
    "purchasing_staff": PURCHASING_STAFF,
    "موظف مستودع": WAREHOUSE_STAFF,
    "warehouse_staff": WAREHOUSE_STAFF,
    "مدير مشتريات": PURCHASING_MANAGER,
    "purchasing_manager": PURCHASING_MANAGER,
    "سوبر ادمن": SUPER_ADMIN,
    "super_admin": SUPER_ADMIN,
    "superadmin": SUPER_ADMIN,
    "admin": SUPER_ADMIN,
}

ROLE_PERMS = {
    PURCHASING_STAFF: {
        "dashboard",
        "requests.view",
        "requests.create",
        "requests.export",
        "requests.issue",
        "suppliers.view",
        "reps.view",
        "settings",
    },
    WAREHOUSE_STAFF: {
        "dashboard",
        "requests.view",
        "requests.receive",
        "schedule.view",
        "schedule.assign",
        "warehouses.view",
        "keepers.view",
        "keepers.manage",
        "settings",
    },
    PURCHASING_MANAGER: {
        "dashboard",
        "requests.view",
        "requests.create",
        "requests.export",
        "requests.issue",
        "schedule.view",
        "suppliers.view",
        "suppliers.manage",
        "reps.view",
        "reps.manage",
        "warehouses.view",
        "warehouses.manage",
        "keepers.view",
        "keepers.manage",
        "departments.view",
        "departments.manage",
        "whatsapp.manage",
        "settings",
    },
    SUPER_ADMIN: {"*"},
}

ROLE_GUIDE = [
    (
        PURCHASING_STAFF,
        "رفع طلبات التوريد وتصديرها والإبلاغ عن مشكلة، مع عرض الموردين فقط.",
    ),
    (
        WAREHOUSE_STAFF,
        "عرض الطلبات وتعليمها كمستلمة، وجدولة التسليم، وإدارة أمناء المستودعات.",
    ),
    (
        PURCHASING_MANAGER,
        "إدارة طلبات التوريد والموردين والمندوبين والأقسام والمستودعات، دون إدارة المستخدمين.",
    ),
    (
        SUPER_ADMIN,
        "كامل الصلاحيات بما فيها إدارة المستخدمين وكل شاشات التهيئة.",
    ),
]


def normalize_role(user):
    if not getattr(user, "is_authenticated", False):
        return ""
    if getattr(user, "is_superuser", False):
        return SUPER_ADMIN
    raw = ""
    try:
        raw = user.profile.role or ""
    except Exception:
        raw = ""
    if raw in ROLE_LABELS:
        return raw
    return ROLE_ALIASES.get(raw, PURCHASING_STAFF)


def role_label(user):
    return ROLE_LABELS.get(normalize_role(user), "")


def apply_role_flags(user, role):
    is_admin = role == SUPER_ADMIN
    user.is_superuser = is_admin
    user.is_staff = is_admin
    return user


def has_perm(user, perm):
    role = normalize_role(user)
    if role == SUPER_ADMIN:
        return True
    return perm in ROLE_PERMS.get(role, set())


def perms_for(user):
    if not getattr(user, "is_authenticated", False):
        return {
            "role": "",
            "role_label": "",
        }
    return {
        "role": normalize_role(user),
        "role_label": role_label(user),
        "requests_view": has_perm(user, "requests.view"),
        "requests_create": has_perm(user, "requests.create"),
        "requests_export": has_perm(user, "requests.export"),
        "requests_issue": has_perm(user, "requests.issue"),
        "requests_receive": has_perm(user, "requests.receive"),
        "schedule_view": has_perm(user, "schedule.view"),
        "schedule_assign": has_perm(user, "schedule.assign"),
        "departments_view": has_perm(user, "departments.view"),
        "departments_manage": has_perm(user, "departments.manage"),
        "warehouses_view": has_perm(user, "warehouses.view"),
        "warehouses_manage": has_perm(user, "warehouses.manage"),
        "suppliers_view": has_perm(user, "suppliers.view"),
        "suppliers_manage": has_perm(user, "suppliers.manage"),
        "reps_view": has_perm(user, "reps.view"),
        "reps_manage": has_perm(user, "reps.manage"),
        "keepers_view": has_perm(user, "keepers.view"),
        "keepers_manage": has_perm(user, "keepers.manage"),
        "users_manage": has_perm(user, "users.manage"),
        "whatsapp_manage": has_perm(user, "whatsapp.manage"),
        "settings": has_perm(user, "settings"),
        "is_super_admin": normalize_role(user) == SUPER_ADMIN,
    }


def require_perm(perm):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not has_perm(request.user, perm):
                messages.warning(request, "ليست لديك صلاحية الوصول إلى هذه الصفحة")
                return redirect("dashboard")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def deny_unless(request, perm):
    if has_perm(request.user, perm):
        return None
    messages.warning(request, "ليست لديك صلاحية تنفيذ هذا الإجراء")
    return redirect("dashboard")
