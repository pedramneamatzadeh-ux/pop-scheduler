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
| ⚪ در صف اجرا | تست نهایی روی سرور |
| 🟢 انجام شده | بازنویسی کامل بر اساس الگوهای Uploader-Bot |

---

## 🟢 انجام شده

| # | مورد | جزئیات |
|---|---|---|
| 1 | بازنویسی `config.py` | استفاده از `Config` class با type hints و validation |
| 2 | بازنویسی `constants.py` | Stateها با `range()` + `Msg` class برای پیام‌ها |
| 3 | ساخت `decorators.py` | `@owner_only` و `@admin_required` با type hints کامل |
| 4 | بازنویسی `utils.py` | اضافه کردن `normalize_digits`, `parse_message_ids`, `validate_hour_input`, `get_month_days`, `is_admin_or_owner` |
| 5 | بازنویسی `keyboards.py` | اضافه کردن `ib()` helper با رنگ خودکار، اصلاح نمایش دکمه‌ها |
| 6 | بازنویسی `handlers/schedule.py` | رفع مشکلات conversation، اصلاح فرمت ساعت، دکمه‌های تاریخ |
| 7 | بازنویسی `handlers/settings.py` | رفع مشکل بسته شدن conversation، اصلاح فرمت ساعت |
| 8 | بازنویسی `handlers/base.py` | استفاده از `config` object به جای متغیرهای مستقیم |
| 9 | به‌روزرسانی `handlers/posts.py` | سازگاری با `config` object |
| 10 | به‌روزرسانی `handlers/history.py` | سازگاری با `config` object |
| 11 | به‌روزرسانی `application.py` | ساختار تمیزتر، رفع مشکل `per_message` |

---

## 🔧 مشکلات رفع‌شده

### P1: دکمه‌های ریپلای کیبورد کار نمی‌کردند
**علت:** استفاده از `per_message=True` در ConversationHandler  
**رفع:** حذف `per_message` از همه ConversationHandlerها

### P2: بسته شدن conversation بعد از فرمت اشتباه
**علت:** بازگشت به `ConversationHandler.END` به جای state فعلی  
**رفع:** بازگشت به state مربوطه (مثلاً `INPUT_YEAR`, `INPUT_DAY`, `INPUT_HOUR`, `CUSTOM_HOUR_INPUT`)

### P3: فرمت ساعت باید `HH:MM` باشد
**علت:** قبول فقط عدد ساده  
**رفع:** اضافه کردن `validate_hour_input()` که هم `14` و هم `14:30` را قبول می‌کند

### P4: دکمه ماه فقط نام ماه را نشان دهد
**علت:** نمایش سال هم همراه ماه  
**رفع:** اصلاح `datetime_keyboard()` برای نمایش فقط نام ماه

### P5: دکمه سال جداگانه
**علت:** نبود دکمه مستقل برای سال  
**رفع:** اضافه کردن دکمه "📅 2026" با callback `dt:year`

### P6: دکمه روز تعداد روزهای ماه را بداند
**علت:** عدم اطلاع از تعداد روزهای ماه  
**رفع:** استفاده از `get_month_days()` و نمایش "📆 15 (از 1 تا 31)"

---

## 📝 تغییرات ساختاری

### قبل (Uploader-Bot الگو نبود)
```python
# config.py
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
```

### بعد (الگوی Uploader-Bot)
```python
# config.py
class Config:
    def __init__(self) -> None:
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
        self.OWNER_ID: Optional[int] = self._parse_optional_id(os.getenv("OWNER_ID"))
    
    def validate(self) -> None:
        if not self.BOT_TOKEN:
            raise ValueError("...")

config = Config()
```

### قبل (Stateها)
```python
MAIN_MENU = 0
SELECT_SOURCE_CHANNEL = 1
SELECT_MESSAGE_IDS = 2
```

### بعد (الگوی Uploader-Bot)
```python
(
    SELECT_SOURCE_CHANNEL,
    SELECT_MESSAGE_IDS,
    SELECT_DATETIME,
    INPUT_YEAR,
    INPUT_DAY,
    INPUT_HOUR,
    SELECT_TARGET_CHANNEL,
    CONFIRM_SCHEDULE,
) = range(8)
```

### قبل (Keyboards)
```python
InlineKeyboardButton("🗓 November 2026", callback_data="dt:month")
```

### بعد (الگوی Uploader-Bot)
```python
def ib(text: str, style: Optional[str] = None, **kwargs):
    if style is None:
        if "لغو" in text:
            style = "danger"
    return InlineKeyboardButton(text, style=style, **kwargs)

ib(f"🗓 {month_name}", callback_data="dt:month")
```

---

## 🔵 مشکلات / پیشنهادهای کشف‌شده

| # | مورد | توضیح |
|---|---|---|
| S1 | پشتیبانی از media group | فعلاً فقط تک‌پیام پشتیبانی می‌شود |
| S2 | تکرار پست | قابلیت تکرار خودکار (cron) پیاده‌سازی نشده |
| S3 | پیش‌نمایش پست | ادمین بتواند قبل از تأیید، پست را پیش‌نمایش کند |
| S4 | آمار ارسال‌ها | پنل آمار (تعداد موفق/ناموفق) پیاده‌سازی نشده |

---

## 📌 یادداشت‌های مهم

- تمام فایل‌های پایه (`config.py`, `constants.py`, `decorators.py`, `utils.py`, `keyboards.py`) بر اساس الگوهای Uploader-Bot بازنویسی شده‌اند
- type hints در همه جا اضافه شده است
- error handling بهبود یافته است
- conversationها بعد از خطا بسته نمی‌شوند
- فرمت ساعت `HH:MM` پشتیبانی می‌شود
- دکمه‌های تاریخ و ساعت بهبود یافته‌اند

---

## 📊 آمار کد

| بخش | قبل | بعد | تغییر |
|---|---|---|---|
| فایل‌های پایه | ۵ | ۵ | بازنویسی کامل |
| Handlers | ۵ | ۵ | بازنویسی کامل |
| Database | ۴ | ۴ | بدون تغییر |
| Services | ۲ | ۲ | بدون تغییر |
| Tests | ۳ | ۳ | بدون تغییر |
| **مجموع خطوط** | ~۳۳۵۰ | ~۳۵۰۰ | +۱۵۰ |

---

## ✅ وضعیت تست‌ها

- ✅ Import tests: همه ماژول‌ها import می‌شوند
- ✅ Database tests: ۱۱/۱۱ موفق
- ✅ Utils tests: ۹/۹ موفق
- ⏳ Integration tests: نیاز به تست روی سرور
