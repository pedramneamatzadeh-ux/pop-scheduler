# 📋 لیست تغییرات و وضعیت پروژه ربات زمان‌بندی پست

> این فایل مرجع زنده پروژه است و باید بعد از هر تغییر به‌روزرسانی شود.
> مرجع قوانین همکاری: [`INSTRUCTIONS.md`](INSTRUCTIONS.md)
> آخرین به‌روزرسانی: ۲۰۲۶-۱۱-۰۹

---

## 🗂️ خلاصه وضعیت پروژه

| وضعیت | موارد |
|---|---|
| 🔴 در حال بررسی | (خالی) |
| 🟡 در انتظار تصمیم | (خالی) |
| ⚪ در صف اجرا | (خالی) |
| 🟢 انجام شده | ساختار اولیه پروژه + نسخه پایه v0.1.0 |

---

## 🟢 انجام شده

| # | مورد | جزئیات |
|---|---|---|
| 1 | ساختار اولیه پروژه | پوشه‌های `bot/`, `bot/database/`, `bot/handlers/`, `bot/services/`, `tests/` |
| 2 | `INSTRUCTIONS.md` | دستورالعمل کامل همکاری |
| 3 | `CHANGE_LIST.md` | همین فایل |
| 4 | `config.py` | مدیریت تنظیمات از env (BOT_TOKEN, OWNER_ID, DATABASE, ADMIN_IDS, CHANNELS, TIMEZONE) |
| 5 | `constants.py` | تمام ثابت‌ها، پیام‌ها و stateهای ConversationHandler |
| 6 | `database/core.py` | اتصال SQLite + WAL + migration + جدول‌های اصلی |
| 7 | `database/scheduler_db.py` | عملیات CRUD پست‌های زمان‌بندی‌شده |
| 8 | `database/settings_db.py` | مدیریت کانال‌ها، ادمین‌ها و ساعت‌های پیش‌فرض |
| 9 | `utils.py` | توابع کمکی (parse date/time, extract message data, pagination, decorators) |
| 10 | `keyboards.py` | تمام کیبوردهای Reply و Inline |
| 11 | `services/scheduler.py` | مدیریت APScheduler برای زمان‌بندی پست‌ها |
| 12 | `services/delivery.py` | ارسال پست به کانال (با پشتیبانی از تمام انواع محتوا) |
| 13 | `handlers/base.py` | start, cancel, main menu, error handler |
| 14 | `handlers/schedule.py` | فلوی کامل زمان‌بندی جدید (پیام → کانال → تاریخ → ساعت → تأیید) |
| 15 | `handlers/posts.py` | مدیریت پست‌های فعال (مشاهده، ویرایش تاریخ/ساعت/کانال، حذف، لغو) |
| 16 | `handlers/settings.py` | تنظیمات (کانال‌ها، ساعت‌ها، ادمین‌ها) |
| 17 | `handlers/history.py` | تاریخچه ارسال‌ها |
| 18 | `application.py` | اتصال تمام handlerها و ConversationHandlerها |
| 19 | `main.py` | نقطه شروع ربات |
| 20 | `requirements.txt` | وابستگی‌ها (python-telegram-bot>=22.7, python-dotenv, APScheduler) |
| 21 | `.env.example` | نمونه فایل env |

---

## 📝 توضیحات معماری نسخه پایه

### ساختار فایل‌ها

```
pop-scheduler/
├── bot/
│   ├── __init__.py
│   ├── main.py           # نقطه شروع
│   ├── config.py         # تنظیمات از env
│   ├── constants.py      # ثابت‌ها + stateها + پیام‌ها
│   ├── keyboards.py      # Reply + Inline keyboards
│   ├── utils.py          # توابع کمکی + decoratorها
│   ├── application.py    # ساخت Application + اتصال handlerها
│   ├── database/
│   │   ├── __init__.py   # Database class + singleton
│   │   ├── core.py       # اتصال SQLite + migration
│   │   ├── scheduler_db.py  # CRUD پست‌های زمان‌بندی
│   │   └── settings_db.py   # کانال‌ها، ادمین‌ها، ساعت‌ها
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── base.py       # /start, /cancel, منوی اصلی
│   │   ├── schedule.py   # فلوی زمان‌بندی جدید
│   │   ├── posts.py      # مدیریت پست‌های فعال
│   │   ├── settings.py   # تنظیمات
│   │   └── history.py    # تاریخچه
│   └── services/
│       ├── __init__.py
│       ├── scheduler.py  # APScheduler
│       └── delivery.py   # ارسال پیام
├── tests/
├── .env.example
├── requirements.txt
├── INSTRUCTIONS.md
├── CHANGE_LIST.md
└── LICENSE
```

### معماری

| بخش | توضیح |
|---|---|
| **زبان** | Python 3.11+ |
| **کتابخانه تلگرام** | `python-telegram-bot>=22.7` (آخرین Bot API) |
| **زمان‌بندی** | APScheduler 3.x (AsyncIOScheduler) |
| **دیتابیس** | SQLite3 + WAL mode |
| **تاریخ** | میلادی (طبق درخواست کاربر) |
| **ساعت‌های پیش‌فرض** | 08, 11, 14, 17, 20, 23 |
| **Timezone** | Europe/Berlin (پیش‌فرض) |
| **احراز هویت** | OWNER_ID + ADMIN_IDS (دیتابیس) |

### ConversationHandlerها

| # | مکالمه | Stateها |
|---|---|---|
| 1 | زمان‌بندی جدید | AWAITING_POST → SELECT_CHANNEL → SELECT_DATE → SELECT_TIME → CUSTOM_TIME → CONFIRM_SCHEDULE |
| 2 | مدیریت پست‌ها | MANAGE_POSTS → MANAGE_POST_DETAIL → EDIT_POST_DATE/EDIT_POST_TIME → EDIT_CUSTOM_TIME |
| 3 | تاریخچه | VIEW_HISTORY |
| 4 | تنظیمات | SETTINGS_MENU → ADD_CHANNEL → ADD_ADMIN → CUSTOM_HOUR_INPUT |

### جدول‌های دیتابیس

| جدول | توضیح |
|---|---|
| `scheduled_posts` | پست‌های زمان‌بندی‌شده (message_data, target_channel, schedule_date/time, status) |
| `settings` | تنظیمات کلید-مقدار |
| `channels` | کانال‌های مجاز |
| `admins` | مدیران ربات |
| `post_history` | لاگ تغییرات پست‌ها |

### فلوی اصلی

```
ادمین → ربات → پیام (متن/عکس/ویدیو/...)
                 ↓
          انتخاب کانال مقصد
                 ↓
          انتخاب تاریخ (امروز/فردا/پس‌فردا/دلخواه)
                 ↓
          انتخاب ساعت (پیش‌فرض/دلخواه)
                 ↓
          تأیید → ذخیره در DB + زمان‌بندی با APScheduler
                 ↓
          سر وقت → ارسال به کانال با send_photo/video/...
                   (یا copy_message برای forward بدون نمایش فرستنده)
```

---

## 🔵 مشکلات / پیشنهادهای کشف‌شده

| # | مورد | توضیح |
|---|---|---|
| S1 | پشتیبانی از media group (آلبوم) | فعلاً فقط تک‌پیام پشتیبانی می‌شود. برای آلبوم‌ها باید `send_media_group` پیاده‌سازی شود. |
| S2 | بازیابی فایل‌ها پس از ری‌استارت | اگر ربات ری‌استارت شود، file_idها معتبرند ولی اگر تلگرام آنها را پاک کند، ارسال ناموفق می‌شود. پیشنهاد: ذخیره فایل‌ها روی دیسک. |
| S3 | فوروارد بدون نمایش فرستنده | فعلاً پیام‌ها به صورت مستقیم ارسال می‌شوند. برای فوروارد ناشناس باید `copy_message` استفاده شود. فعلاً `send_copy()` در delivery.py آماده است. |
| S4 | آمار ارسال‌ها | هنوز پنل آمار (تعداد ارسال موفق/ناموفق، بیشترین کانال و...) پیاده‌سازی نشده. |
| S5 | تکرار پست | قابلیت تکرار خودکار (مثلاً هر روز ساعت ۲۰) فعلاً پیاده‌سازی نشده. APScheduler از cron trigger پشتیبانی می‌کند. |
| S6 | ارسال گروهی به چند کانال | فعلاً هر پست فقط به یک کانال می‌رود. قابلیت ارسال به چند کانال همزمان می‌تواند اضافه شود. |
| S7 | پیش‌نمایش پست قبل از زمان‌بندی | ادمین بتواند قبل از تأیید نهایی، پست را در یک چت خصوصی پیش‌نمایش کند. |
| S8 | اولویت‌بندی پیام‌ها | اگر چند پست در یک زمان باشند، ترتیب ارسال مشخص نیست. |

---

## 📌 یادداشت‌های مهم

- ساعت‌های پیش‌فرض: `08:00, 11:00, 14:00, 17:00, 20:00, 23:00`
- تاریخ‌ها به صورت میلادی (Gregorian)
- ربات از `copy_message` برای ارسال بدون نمایش فرستنده پشتیبانی می‌کند
- دیتابیس SQLite با WAL mode برای عملکرد بهتر
- ماژولار: handlerها و serviceها جدا هستند
