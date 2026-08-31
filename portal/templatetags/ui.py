from django import template
from django.urls import reverse

register = template.Library()

ACTION_META = {
    "view": {"label": "عرض", "icon": "eye"},
    "edit": {"label": "تعديل", "icon": "edit"},
    "delete": {"label": "حذف", "icon": "trash"},
    "issue": {"label": "الإبلاغ عن مشكلة", "icon": "alert"},
    "receive": {"label": "تعليم كمستلم", "icon": "check"},
}

POST_KINDS = {"delete", "issue", "receive"}


@register.inclusion_tag("partials/action.html", takes_context=True)
def action(context, kind, url_name, pk, item=""):
    meta = ACTION_META.get(kind) or ACTION_META["view"]
    confirm = ""
    if kind == "delete":
        confirm = f"هل تريد حذف {item}؟" if item else "هل تريد الحذف؟"
    return {
        "kind": kind,
        "href": reverse(str(url_name), args=[pk]),
        "label": meta["label"],
        "icon": meta["icon"],
        "is_post": kind in POST_KINDS,
        "confirm": confirm,
        "csrf_token": context.get("csrf_token"),
    }
