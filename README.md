# هذا المشروع تم إنشاؤه كقاعدة قابلة للتعديل لتطوير نظام تلقائي لجمع عروض العمل وإرسال تنبيهات البريد الإلكتروني.

## المميزات
- جمع عروض العمل من بريد الوارد عبر IMAP
- استخراج معلومات الوظيفة من الرسالة (العنوان، الدولة، الرابط، التفاصيل)
- حفظ البيانات في قاعدة SQLite/SQLAlchemy
- إرسال تنبيهات عبر SMTP إلى المشتركين
- جدولة تلقائية باستخدام APScheduler
- سجل كامل للأخطاء والمعاملات
- بنية قابلة للتوسيع بسهولة

## متطلبات التشغيل
- Python 3.10+
- pip

## تركيب المشروع
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# أو:
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
cp .env.example .env
```

## إعداد متغيرات البيئة
عدّل ملف `.env` حسب إعدادات بريدك الإلكتروني وقاعدة البيانات.

## التشغيل
```bash
python main.py
```

## هيكل المشروع
```text
jobs-automation-system/
├── config/
│   ├── __init__.py
│   └── settings.py
├── database/
│   ├── __init__.py
│   ├── database.py
│   └── models.py
├── services/
│   ├── __init__.py
│   ├── alert_dispatcher.py
│   ├── email_receiver.py
│   ├── email_sender.py
│   └── job_parser.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── validators.py
├── .env.example
├── .gitignore
├── main.py
├── README.md
├── requirements.txt
└── .venv/
```

## ملاحظات هامة
- استخدم كلمة مرور تطبيق Gmail إذا كنت تستخدم Gmail.
- لا تضع كلمات المرور مباشرة داخل الكود، استخدم ملف `.env`.
- SQLite مناسب للاختبار والتطوير، ويمكن التبديل إلى PostgreSQL لاحقاً.

## تطوير لاحق
- إضافة واجهة ويب
- دعم تحليل HTML أفضل
- ربط قاعدة بيانات PostgreSQL
- إضافة اشتراكات حسب الدولة والقطاع
- دعم AI لتحليل المحتوى النصي
