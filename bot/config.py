"""
مدیریت تنظیمات ربات.
بارگذاری از فایل .env و ارائه دسترسی متمرکز.
"""
import os
from typing import List, Optional

from dotenv import load_dotenv


# ریشه پروژه (پوشه‌ای که main.py در آن است) — مستقل از CWD اجرا
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))


class Config:
    """کلاس تنظیمات ربات با type hints و validation."""
    
    DB_PATH: str = os.path.join(_PROJECT_ROOT, "scheduler.db")
    DEFAULT_HOURS: List[int] = [8, 11, 14, 17, 20, 23]
    TIMEZONE: str = "Europe/Berlin"

    def __init__(self) -> None:
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
        self.OWNER_ID: Optional[int] = self._parse_optional_id(
            os.getenv("OWNER_ID")
        )
        self.TIMEZONE = os.getenv("TIMEZONE", self.TIMEZONE)

    @staticmethod
    def _parse_optional_id(raw: Optional[str]) -> Optional[int]:
        """تبدیل رشته به آیدی عددی اختیاری."""
        value = (raw or "").strip()
        if value.isdigit():
            return int(value)
        return None

    def validate(self) -> None:
        """اعتبارسنجی تنظیمات ضروری."""
        if not self.BOT_TOKEN or self.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            raise ValueError(
                "لطفاً BOT_TOKEN را در فایل .env تنظیم کنید."
            )

        if self.OWNER_ID is None:
            raise ValueError(
                "لطفاً OWNER_ID (آیدی عددی تلگرام مالک) را "
                "در فایل .env تنظیم کنید."
            )


# نمونه singleton برای دسترسی آسان
config = Config()
