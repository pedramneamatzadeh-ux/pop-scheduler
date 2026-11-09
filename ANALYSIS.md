# 📊 تحلیل وضعیت فعلی پروژه Pop Scheduler

> تاریخ تحلیل: ۲۰۲۶-۱۱-۰۹  
> مرجع الگو: `Uploader-Bot`

---

## 🔴 مشکلات شناسایی‌شده

### ۱. مشکلات گزارش‌شده توسط کاربر

| # | مشکل | شدت | وضعیت |
|---|---|---|---|
| P1 | دکمه‌های ریپلای کیبورد کار نمی‌کنند | 🔴 بحرانی | باید رفع شود |
| P2 | وقتی فرمت اشتباه وارد می‌شود، conversation بسته می‌شود | 🔴 بحرانی | باید رفع شود |
| P3 | فرمت ساعت باید `HH:MM` باشد | 🟡 متوسط | باید اصلاح شود |
| P4 | دکمه ماه فقط نام ماه را نشان دهد (بدون سال) | 🟢 ساده | باید اصلاح شود |
| P5 | دکمه سال جداگانه اضافه شود | 🟢 ساده | باید اضافه شود |
| P6 | دکمه روز باید تعداد روزهای ماه را بداند | 🟢 ساده | باید اضافه شود |

### ۲. مشکلات معماری

| # | مشکل | راه‌حل پیشنهادی |
|---|---|---|
| A1 | نبود `decorators.py` جداگانه | ساخت فایل `bot/decorators.py` با `@owner_only` و `@admin_only` |
| A2 | `config.py` ساده است، class-based نیست | بازنویسی با `Config` class و type hints |
| A3 | Stateها به صورت عددی تعریف شده‌اند | استفاده از `range()` مثل Uploader-Bot |
| A4 | نبود `ib()` helper برای ساخت دکمه‌ها | اضافه کردن تابع `ib()` با رنگ خودکار |
| A5 | `utils.py` توابع helper کمتری دارد | اضافه کردن `normalize_digits`, `parse_range`, `validate_*` |
| A6 | handlers ماژولار نیستند | ساخت `handlers/schedule/` با فایل‌های جداگانه |
| A7 | نبود type hints در اکثر فایل‌ها | اضافه کردن type hints کامل |

### ۳. مشکلات کد

| # | مشکل | فایل | راه‌حل |
|---|---|---|---|
| C1 | `edit_message_text` با `ReplyKeyboardMarkup` | `schedule.py` | استفاده از `inline_cancel_keyboard()` |
| C2 | Conversation بسته می‌شود بعد از خطا | `settings.py` | بازگشت به state به جای `ConversationHandler.END` |
| C3 | نبود error handling مناسب | همه فایل‌ها | اضافه کردن try/except و logging |
| C4 | کد تکراری در keyboard builders | `keyboards.py` | استفاده از helper functions |

---

## 📋 برنامه بازنویسی

### فاز ۱: زیرساخت (فایل‌های پایه)

1. **`bot/config.py`** - بازنویسی با `Config` class
2. **`bot/constants.py`** - Stateها با `range()` + `Msg` class
3. **`bot/decorators.py`** - فایل جدید با `@owner_only` و `@admin_only`
4. **`bot/utils.py`** - اضافه کردن helper functions
5. **`bot/keyboards.py`** - اضافه کردن `ib()` و رنگ‌ها

### فاز ۲: دیتابیس

1. **`bot/database/core.py`** - بهبود migration و error handling
2. **`bot/database/scheduler_db.py`** - اضافه کردن type hints
3. **`bot/database/settings_db.py`** - بهبود channel types

### فاز ۳: Handlers (ماژولار)

1. **`bot/handlers/base.py`** - start, cancel, main menu
2. **`bot/handlers/schedule/`** - ماژولار کردن:
   - `__init__.py` - exports
   - `start.py` - شروع فلوی زمان‌بندی
   - `channel.py` - انتخاب کانال
   - `datetime.py` - انتخاب تاریخ/ساعت
   - `confirm.py` - تأیید و ذخیره
3. **`bot/handlers/posts.py`** - مدیریت پست‌ها
4. **`bot/handlers/settings.py`** - تنظیمات (فقط مالک)
5. **`bot/handlers/history.py`** - تاریخچه

### فاز ۴: Services

1. **`bot/services/scheduler.py`** - بهبود APScheduler integration
2. **`bot/services/delivery.py`** - بهبود copy_message

### فاز ۵: Application

1. **`bot/application.py`** - بازنویسی با ساختار تمیزتر
2. **`bot/main.py`** - بهبود startup و error handling

---

## 🎯 اولویت‌ها

### فوری (باید قبل از هر چیز دیگری رفع شود)

1. رفع مشکل دکمه‌های ریپلای کیبورد (P1)
2. رفع مشکل بسته شدن conversation (P2)
3. اضافه کردن `decorators.py` (A1)

### کوتاه‌مدت (هفته اول)

4. بازنویسی `config.py` (A2)
5. اصلاح Stateها با `range()` (A3)
6. اضافه کردن `ib()` helper (A4)
7. اصلاح فرمت ساعت (P3)

### میان‌مدت (هفته دوم)

8. ماژولار کردن handlers (A6)
9. اضافه کردن type hints (A7)
10. بهبود keyboard builders (A5)

### بلندمدت (هفته سوم+)

11. اضافه کردن tests
12. بهبود documentation
13. اضافه کردن قابلیت‌های جدید

---

## 📝 یادداشت‌های مهم

- تمام تغییرات باید در `CHANGE_LIST.md` ثبت شوند
- از الگوهای `Uploader-Bot` برای ساختار کد استفاده شود
- type hints در همه جا اضافه شود
- error handling مناسب اضافه شود
- logging بهبود یابد

---

## ✅ وضعیت تغییرات

| # | تغییر | وضعیت | تاریخ |
|---|---|---|---|
| 1 | تحلیل اولیه پروژه | 🟢 انجام شد | ۲۰۲۶-۱۱-۰۹ |
| 2 | بازنویسی `config.py` | 🔴 در انتظار | - |
| 3 | بازنویسی `constants.py` | 🔴 در انتظار | - |
| 4 | ساخت `decorators.py` | 🔴 در انتظار | - |
| 5 | بازنویسی `utils.py` | 🔴 در انتظار | - |
| 6 | بازنویسی `keyboards.py` | 🔴 در انتظار | - |
