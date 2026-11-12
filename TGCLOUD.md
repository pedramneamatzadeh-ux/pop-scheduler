# Pop Scheduler — Telegram Serverless (tgcloud)

## راه‌اندازی سریع

### ۱. فعال‌سازی Serverless در BotFather

1. به @BotFather برو
2. ربات خودت رو انتخاب کن
3. **Serverless** → روشن کن
4. از **CLI Access** → **Access token** رو کپی کن

### ۲. نصب و لاگین

```bash
# در پوشه پروژه
npm install

# لاگین با توکن CLI
npx tgcloud login
# توکن CLI رو از BotFather وارد کن
```

### ۳. Deploy

```bash
# آپلود کد
npx tgcloud push

# ساخت جداول دیتابیس
npx tgcloud migrate
```

### ۴. تست

```bash
# تست handler
npx tgcloud run handlers/message '{ chat: { id: 1 }, from: { id: 5240053330, first_name: "Test" }, text: "/start" }'
```

---

## ساختار پروژه

```
tgcloud/
├─ schema.js                  # جداول SQLite
├─ handlers/
│  ├─ message.js              # هندلر پیام‌ها
│  └─ callback_query.js       # هندلر دکمه‌ها
└─ lib/
   ├─ config.js               # تنظیمات (OWNER_ID, TIMEZONE, DEFAULT_HOURS)
   ├─ constants.js            # پیام‌ها و ثابت‌ها
   ├─ utils.js                # توابع کمکی
   ├─ auth.js                 # بررسی admin/owner
   ├─ keyboards.js            # سازنده‌های keyboard
   ├─ db.js                   # عملیات دیتابیس
   ├─ scheduler.js            # بررسی و ارسال پست‌ها
   ├─ session.js              # مدیریت session
   ├─ schedule-flow.js        # فلوی زمان‌بندی
   ├─ posts-flow.js           # مدیریت پست‌ها
   ├─ settings-flow.js        # تنظیمات
   └─ history-flow.js         # تاریخچه
```

---

## مزایای tgcloud

| ویژگی | توضیح |
|-------|-------|
| **رایگان** | بدون هزینه هاست |
| **بدون پروکسی** | مستقیماً روی زیرساخت تلگرام |
| **بدون سرور** | بدون نیاز به VPS یا Docker |
| **بدون خواب** | همیشه آنلاین |
| **دیتابیس داخلی** | SQLite خودکار |
| **مقیاس‌پذیر** | خودکار scale می‌شه |

---

## محدودیت‌ها

- فقط JavaScript (نه Python)
- بدون npm packages
- بدون file system
- بدون APScheduler (جایگزین: بررسی روی هر update)
- حداکثر ۳۲MB response

---

## دستورات CLI

| دستور | توضیح |
|-------|-------|
| `npx tgcloud init` | ساخت پروژه جدید |
| `npx tgcloud login` | لاگین با توکن |
| `npx tgcloud push` | آپلود کد |
| `npx tgcloud migrate` | اعمال تغییرات دیتابیس |
| `npx tgcloud status` | وضعیت تغییرات |
| `npx tgcloud diff` | جزئیات تغییرات |
| `npx tgcloud run <handler> '<json>'` | تست handler |
