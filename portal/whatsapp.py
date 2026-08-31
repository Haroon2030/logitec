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


def _api_key(config):
    from django.conf import settings as dj_settings

    stored = (getattr(config, "api_key", "") or "").strip()
    env_key = (getattr(dj_settings, "EVOLUTION_API_KEY", "") or "").strip()
    return env_key or stored or "HARO@2030"


def _server_url(config):
    from django.conf import settings as dj_settings

    stored = (getattr(config, "server_url", "") or "").rstrip("/")
    env_url = (getattr(dj_settings, "EVOLUTION_SERVER_URL", "") or "").rstrip("/")
    return stored or env_url or "http://72.61.107.230:8081"


def _call(config, method, path, payload=None, timeout=20):
    base = _server_url(config)
    key = _api_key(config)
    name = (config.instance_name or "").strip()
    if not base or not key:
        raise RuntimeError("أكمل بيانات سيرفر Evolution أولاً")
    url = f"{base}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("apikey", key)
    request.add_header("Authorization", f"Bearer {key}")
    request.add_header("Accept", "application/json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(
            request, timeout=timeout, context=_ssl_context(config.verify_ssl)
        ) as response:
            body = response.read().decode("utf-8") or "{}"
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"raw": body}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 401:
            raise RuntimeError("مفتاح API مرفوض. استخدم HARO@2030 ثم احفظ") from exc
        raise RuntimeError(f"{exc.code}: {detail[:240]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason or exc)) from exc


def connection_state(config):
    name = (config.instance_name or "").strip()
    try:
        data = _call(config, "GET", f"/instance/connectionState/{name}")
        instance = data.get("instance") if isinstance(data, dict) else {}
        if isinstance(instance, dict):
            state = instance.get("state") or data.get("state") or ""
            if state:
                return state
        if isinstance(data, dict) and data.get("state"):
            return data.get("state")
    except RuntimeError:
        pass
    instances = _call(config, "GET", "/instance/fetchInstances")
    rows = instances if isinstance(instances, list) else [instances]
    for item in rows:
        if not isinstance(item, dict):
            continue
        if (item.get("name") or item.get("instanceName")) == name:
            return item.get("connectionStatus") or item.get("status") or ""
    return ""


def qr_image_src(value):
    if not value:
        return ""
    value = str(value).strip()
    if value.startswith("data:"):
        return value
    return "data:image/png;base64," + value.replace("\n", "").replace(" ", "")


def ensure_instance(config):
    payloads = (
        {
            "instanceName": config.instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
        },
        {"instanceName": config.instance_name, "qrcode": True},
    )
    last_error = None
    for payload in payloads:
        try:
            return _call(config, "POST", "/instance/create", payload)
        except RuntimeError as exc:
            last_error = exc
            text = str(exc).lower()
            if "exist" in text or "already" in text or "403" in text:
                return {"ok": True}
    if last_error and "404" not in str(last_error):
        raise last_error
    return None


def fetch_connect(config):
    try:
        data = _call(config, "GET", f"/instance/connect/{config.instance_name}", timeout=45)
    except RuntimeError as exc:
        if "404" in str(exc):
            ensure_instance(config)
            data = _call(config, "GET", f"/instance/connect/{config.instance_name}", timeout=45)
        else:
            raise
    qr = ""
    pairing = ""
    state = ""
    if isinstance(data, dict):
        qr = data.get("base64") or ""
        inner = data.get("qrcode")
        if not qr and isinstance(inner, dict):
            qr = inner.get("base64") or ""
        pairing = data.get("pairingCode") or data.get("pairing_code") or ""
        instance = data.get("instance")
        if isinstance(instance, dict):
            state = instance.get("state") or ""
        state = state or data.get("state") or ""
    return {
        "state": state,
        "qr": qr_image_src(qr),
        "pairing": pairing,
    }


def logout_instance(config):
    return _call(config, "DELETE", f"/instance/logout/{config.instance_name}")


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
