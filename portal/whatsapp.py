import json
import ssl
import urllib.error
import urllib.request

from django.utils import timezone


def normalize_phone(raw):
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


def recipient_list(config):
    return [
        ("المندوب", normalize_phone(config.phone_rep)),
        ("مسؤول المستودع", normalize_phone(config.phone_warehouse)),
        ("المشتريات", normalize_phone(config.phone_purchasing)),
    ]


def _ssl_context(verify_ssl):
    if verify_ssl:
        return ssl.create_default_context()
    return ssl._create_unverified_context()


def _call(config, method, path, payload=None):
    base = (config.server_url or "").rstrip("/")
    if not base or not config.api_key or not config.instance_name:
        raise RuntimeError("أكمل بيانات سيرفر Evolution أولاً")
    url = f"{base}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("apikey", config.api_key)
    request.add_header("Accept", "application/json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(
            request, timeout=20, context=_ssl_context(config.verify_ssl)
        ) as response:
            body = response.read().decode("utf-8") or "{}"
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"{exc.code}: {detail[:240]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason or exc)) from exc


def connection_state(config):
    path = f"/instance/connectionState/{config.instance_name}"
    data = _call(config, "GET", path)
    instance = data.get("instance") if isinstance(data, dict) else {}
    if isinstance(instance, dict):
        return instance.get("state") or data.get("state") or ""
    return data.get("state") if isinstance(data, dict) else ""


def send_text(config, number, text):
    path = f"/message/sendText/{config.instance_name}"
    payloads = (
        {"number": number, "text": text},
        {"number": number, "textMessage": {"text": text}},
    )
    last_error = None
    for payload in payloads:
        try:
            return _call(config, "POST", path, payload)
        except RuntimeError as exc:
            last_error = exc
            if "404" in str(exc) or "400" in str(exc):
                continue
            raise
    raise last_error or RuntimeError("تعذر إرسال الرسالة")


def build_supply_message(obj):
    when = timezone.localtime(obj.placed_at or obj.created_at)
    warehouse = obj.warehouse.name if obj.warehouse else "—"
    city = obj.warehouse.city if obj.warehouse and obj.warehouse.city else ""
    if city:
        warehouse = f"{warehouse} — {city}"
    creator = ""
    if obj.created_by:
        creator = obj.created_by.get_full_name() or obj.created_by.username
    return (
        "أمر توريد جديد\n"
        f"رقم الطلب: {obj.number}\n"
        f"المورد: {obj.supplier.name if obj.supplier else '—'}\n"
        f"المستودع: {warehouse}\n"
        f"الأولوية: {obj.get_priority_display()}\n"
        f"بواسطة المشتريات: {creator or '—'}\n"
        f"التاريخ: {when.strftime('%Y-%m-%d %H:%M')}\n"
        "يرجى المتابعة."
    )


def notify_supply_saved(obj):
    from .models import WhatsAppConfig

    config = WhatsAppConfig.load()
    if not config.enabled:
        return False, "إشعارات واتساب غير مفعّلة"
    text = build_supply_message(obj)
    sent = []
    errors = []
    for label, number in recipient_list(config):
        if not number:
            errors.append(f"{label}: لا يوجد رقم")
            continue
        try:
            send_text(config, number, text)
            sent.append(label)
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    if sent and not errors:
        return True, "تم إرسال واتساب إلى " + "، ".join(sent)
    if sent:
        return True, "أُرسل إلى " + "، ".join(sent) + " — " + "؛ ".join(errors)
    return False, "؛ ".join(errors) or "لا توجد أرقام للمستلمين"
