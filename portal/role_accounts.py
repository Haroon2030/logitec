from django.contrib.auth.models import User

from .models import UserProfile
from .roles import (
    PURCHASING_MANAGER,
    PURCHASING_STAFF,
    ROLE_ALIASES,
    ROLE_LABELS,
    SUPER_ADMIN,
    WAREHOUSE_STAFF,
    apply_role_flags,
)

DEMO_ACCOUNTS = [
    {
        "username": "1",
        "first_name": "أحمد",
        "last_name": "محمود",
        "email": "ahmed.m@logistics-hub.com",
        "role": PURCHASING_MANAGER,
        "phone": "+971 50 123 4567",
        "password": "526400",
    },
    {
        "username": "2",
        "first_name": "سارة",
        "last_name": "علي",
        "email": "sara.ali@logistics-hub.com",
        "role": PURCHASING_STAFF,
        "phone": "+971 50 222 3344",
        "password": "526400",
    },
    {
        "username": "3",
        "first_name": "خالد",
        "last_name": "المستودع",
        "email": "khaled.wh@logistics-hub.com",
        "role": WAREHOUSE_STAFF,
        "phone": "+971 50 555 6677",
        "password": "526400",
    },
    {
        "username": "admin",
        "first_name": "سوبر",
        "last_name": "ادمن",
        "email": "admin@logistics-hub.com",
        "role": SUPER_ADMIN,
        "phone": "",
        "password": "admin123",
    },
]


def normalize_existing_roles():
    for profile in UserProfile.objects.select_related("user"):
        raw = profile.role or ""
        code = raw if raw in ROLE_LABELS else ROLE_ALIASES.get(raw, PURCHASING_STAFF)
        if profile.user.is_superuser:
            code = SUPER_ADMIN
        if profile.role != code:
            profile.role = code
            profile.save(update_fields=["role"])
        apply_role_flags(profile.user, code)
        profile.user.save(update_fields=["is_superuser", "is_staff"])


def ensure_demo_accounts(reset_password=False):
    created = []
    for item in DEMO_ACCOUNTS:
        user, was_created = User.objects.get_or_create(
            username=item["username"],
            defaults={
                "email": item["email"],
                "first_name": item["first_name"],
                "last_name": item["last_name"],
            },
        )
        user.email = item["email"]
        user.first_name = item["first_name"]
        user.last_name = item["last_name"]
        apply_role_flags(user, item["role"])
        if was_created or reset_password:
            user.set_password(item["password"])
        user.save()
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "role": item["role"],
                "phone": item["phone"],
                "branch": "فرع دبي الرئيسي",
                "timezone_name": "GST",
                "language": "ar",
            },
        )
        if was_created:
            created.append(item["username"])
    return created
