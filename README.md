# LogisticsPro — منصة تنسيق التوريد

مشروع Django لتنسيق طلبات التوريد: دائرة المشتريات ترفع الملفات وتُرسلها إلى المورد والمستودع.

## التشغيل

```powershell
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

ثم افتح [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## حساب تجريبي

- سوبر ادمن: `1`
- كلمة المرور: `526400`

## الصفحات

- `/login/` تسجيل الدخول
- `/` لوحة القيادة
- `/requests/` طلبات التوريد
- `/requests/<id>/` تفاصيل الطلب وتتبع الشحنة
- `/schedule/` جدول المستودع مع سحب وإفلات
- `/settings/` الملف الشخصي والإعدادات
