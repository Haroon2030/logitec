import base64
import json
import mimetypes
import ssl
import urllib.error
import urllib.request
from pathlib import Path

from django.utils import timezone


def normalize_phone(raw):
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


def user_whatsapp_phones(role_codes):
    from .models import UserProfile

    rows = []
    for profile in (
        UserProfile.objects.select_related("user")
        .filter(role__in=role_codes)
        .exclude(phone="")
    ):
        number = normalize_phone(profile.phone)
        if not number:
            continue
        name = profile.user.get_full_name() or profile.user.username
        rows.append((name, number))
    return rows


def recipient_list(config, warehouse=None):
    from .models import Representative, WarehouseKeeper
    from .roles import PURCHASING_MANAGER, PURCHASING_STAFF, WAREHOUSE_STAFF

    rows = []
    seen = set()

    def add(label, number):
        number = normalize_phone(number)
        if not number or number in seen:
            return False
        seen.add(number)
        rows.append((label, number))
        return True

    for rep in Representative.objects.exclude(phone=""):
        add(f"المندوب ({rep.name})", rep.phone)
    add("المندوب", config.phone_rep)

    keepers = WarehouseKeeper.objects.exclude(phone="").prefetch_related("warehouses")
    if warehouse is not None:
        keepers = keepers.filter(warehouses=warehouse)
    keeper_added = False
    for keeper in keepers:
        if add(f"أمين المستودع ({keeper.name})", keeper.phone):
            keeper_added = True
    warehouse_users = False
    for name, number in user_whatsapp_phones([WAREHOUSE_STAFF]):
        if add(f"موظف مستودع ({name})", number):
            warehouse_users = True
    if not keeper_added and not warehouse_users:
        add("مسؤول المستودع", config.phone_warehouse)

    purchasing_added = False
    for name, number in user_whatsapp_phones([PURCHASING_STAFF, PURCHASING_MANAGER]):
        if add(f"المشتريات ({name})", number):
            purchasing_added = True
    if not purchasing_added:
        add("المشتريات", config.phone_purchasing)
    return rows


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


def _read_file_bytes(field_file):
    field_file.open("rb")
    try:
        return field_file.read()
    finally:
        field_file.close()


def request_attachments(obj):
    items = []
    for row in obj.files.all():
        if not row.file:
            continue
        items.append((row.file, row.name))
    if not items and obj.attachment:
        name = obj.attachment.name.rsplit("/", 1)[-1]
        items.append((obj.attachment, name))
    return items


def send_document(config, number, caption, filename, raw_bytes, mime="application/pdf"):
    path = f"/message/sendMedia/{config.instance_name}"
    encoded = base64.b64encode(raw_bytes).decode("ascii")
    payloads = (
        {
            "number": number,
            "mediatype": "document",
            "mimetype": mime,
            "caption": caption,
            "fileName": filename,
            "media": f"data:{mime};base64,{encoded}",
        },
        {
            "number": number,
            "mediatype": "document",
            "mimetype": mime,
            "caption": caption,
            "fileName": filename,
            "media": encoded,
        },
    )
    last_error = None
    for payload in payloads:
        try:
            return _call(config, "POST", path, payload, timeout=90)
        except RuntimeError as exc:
            last_error = exc
            if "404" in str(exc) or "400" in str(exc):
                continue
            raise
    raise last_error or RuntimeError("تعذر إرسال الملف")


def send_supply_whatsapp(config, number, text, attachments):
    if not attachments:
        return send_text(config, number, text)
    last = None
    for index, (field_file, filename) in enumerate(attachments):
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        caption = text if index == 0 else f"مرفق إضافي لأمر التوريد"
        raw = _read_file_bytes(field_file)
        if not raw:
            continue
        safe_name = Path(filename).name or f"tawreed-{index + 1}.pdf"
        last = send_document(config, number, caption, safe_name, raw, mime)
    return last or send_text(config, number, text)


def public_reply_url(obj, request=None):
    from django.conf import settings as dj_settings
    from django.urls import reverse

    path = reverse("supply_rep_reply", args=[obj.reply_token])
    if request is not None:
        return request.build_absolute_uri(path)
    base = (getattr(dj_settings, "PUBLIC_SITE_URL", "") or "").rstrip("/")
    return f"{base}{path}" if base else path


def warehouse_label(obj):
    warehouse = obj.warehouse.name if obj.warehouse else "—"
    city = obj.warehouse.city if obj.warehouse and obj.warehouse.city else ""
    if city:
        return f"{warehouse} — {city}"
    return warehouse


def build_supply_message(obj):
    when = timezone.localtime(obj.placed_at or obj.created_at)
    creator = ""
    if obj.created_by:
        creator = obj.created_by.get_full_name() or obj.created_by.username
    return (
        "أمر توريد جديد\n"
        f"رقم الطلب: {obj.number}\n"
        f"المورد: {obj.supplier.name if obj.supplier else '—'}\n"
        f"المستودع: {warehouse_label(obj)}\n"
        f"الأولوية: {obj.get_priority_display()}\n"
        f"بواسطة المشتريات: {creator or '—'}\n"
        f"التاريخ: {when.strftime('%Y-%m-%d %H:%M')}\n"
        "يرجى المتابعة."
    )


def build_rep_invite_message(obj, reply_url):
    return (
        "أمر توريد جديد\n"
        f"رقم الطلب: {obj.number}\n"
        f"المورد: {obj.supplier.name if obj.supplier else '—'}\n"
        f"المستودع: {warehouse_label(obj)}\n"
        f"الأولوية: {obj.get_priority_display()}\n"
        "حدد تاريخ التوريد وساعة الوصول من الرابط:\n"
        f"{reply_url}"
    )


def build_warehouse_arrival_message(obj):
    hour = f"{int(obj.scheduled_hour):02d}:00" if obj.scheduled_hour is not None else "—"
    day = obj.scheduled_date.strftime("%Y-%m-%d") if obj.scheduled_date else "—"
    return (
        "تأكيد وصول من المندوب\n"
        f"رقم الطلب: {obj.number}\n"
        f"المورد: {obj.supplier.name if obj.supplier else '—'}\n"
        f"المستودع: {warehouse_label(obj)}\n"
        f"تاريخ التوريد: {day}\n"
        f"ساعة الوصول: {hour}\n"
        "يرجى الاستعداد للاستلام."
    )


def notify_supply_saved(obj, request=None):
    from .models import WhatsAppConfig

    config = WhatsAppConfig.load()
    if not config.enabled:
        return False, "إشعارات واتساب غير مفعّلة"
    attachments = request_attachments(obj)
    reply_url = public_reply_url(obj, request)
    staff_text = build_supply_message(obj)
    rep_text = build_rep_invite_message(obj, reply_url)
    sent = []
    errors = []
    for label, number in recipient_list(config, warehouse=obj.warehouse):
        if not number:
            errors.append(f"{label}: لا يوجد رقم")
            continue
        text = rep_text if str(label).startswith("المندوب") else staff_text
        try:
            send_supply_whatsapp(config, number, text, attachments)
            sent.append(label)
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    extra = " مع الملف" if attachments else ""
    if sent and not errors:
        return True, "تم إرسال واتساب" + extra + " إلى " + "، ".join(sent)
    if sent:
        return True, "أُرسل إلى " + "، ".join(sent) + " — " + "؛ ".join(errors)
    return False, "؛ ".join(errors) or "لا توجد أرقام للمستلمين"


def notify_warehouse_arrival(obj):
    from .models import WhatsAppConfig, WarehouseKeeper
    from .roles import WAREHOUSE_STAFF

    config = WhatsAppConfig.load()
    if not config.enabled:
        return False, "إشعارات واتساب غير مفعّلة"
    text = build_warehouse_arrival_message(obj)
    numbers = []
    if obj.warehouse_id:
        for keeper in WarehouseKeeper.objects.filter(warehouses=obj.warehouse).exclude(phone=""):
            number = normalize_phone(keeper.phone)
            if number and number not in numbers:
                numbers.append(number)
    for _, number in user_whatsapp_phones([WAREHOUSE_STAFF]):
        if number not in numbers:
            numbers.append(number)
    fallback = normalize_phone(config.phone_warehouse)
    if fallback and fallback not in numbers:
        numbers.append(fallback)
    if not numbers:
        return False, "لا يوجد رقم لأمين المستودع"
    errors = []
    sent = 0
    for number in numbers:
        try:
            send_text(config, number, text)
            sent += 1
        except Exception as exc:
            errors.append(str(exc))
    if sent and not errors:
        return True, "أُرسل تأكيد الوصول إلى أمين المستودع"
    if sent:
        return True, "أُرسل التأكيد مع تنبيه: " + "؛ ".join(errors)
    return False, "؛ ".join(errors) or "تعذر إرسال تأكيد الوصول"
