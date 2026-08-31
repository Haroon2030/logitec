from django.urls import reverse

from .roles import has_perm, perms_for


def portal_context(request):
    user = request.user
    if not user.is_authenticated:
        return {
            "nav_items": [],
            "active_nav": "",
            "setup_tab": "",
            "perms": {},
        }

    nav = []
    if has_perm(user, "dashboard"):
        nav.append({"name": "dashboard", "label": "لوحة المعلومات", "icon": "grid", "url": reverse("dashboard")})
    if has_perm(user, "requests.view"):
        nav.append({"name": "requests", "label": "أوامر التوريد", "icon": "docs", "url": reverse("requests")})
    if has_perm(user, "schedule.view"):
        nav.append({"name": "schedule", "label": "جدولة الاستلام", "icon": "calendar", "url": reverse("schedule")})

    children = []
    if has_perm(user, "departments.view"):
        children.append({"name": "departments", "label": "دليل الأقسام", "url": reverse("departments")})
    if has_perm(user, "warehouses.view"):
        children.append({"name": "warehouses", "label": "دليل المستودعات", "url": reverse("warehouses")})
    if has_perm(user, "suppliers.view"):
        children.append({"name": "suppliers", "label": "دليل الموردين", "url": reverse("suppliers")})
    if children:
        nav.append(
            {
                "name": "setup",
                "label": "البيانات المرجعية",
                "icon": "setup",
                "url": children[0]["url"],
                "children": children,
            }
        )
    if has_perm(user, "users.manage"):
        nav.append({"name": "users", "label": "إدارة المستخدمين", "icon": "users", "url": reverse("users")})

    return {
        "nav_items": nav,
        "active_nav": getattr(request, "active_nav", ""),
        "setup_tab": getattr(request, "setup_tab", ""),
        "perms": perms_for(user),
    }
