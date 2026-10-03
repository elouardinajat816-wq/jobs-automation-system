import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """القيم الأساسية للتطبيق - مع التحقق من الأمان"""

    # البريد الإلكتروني (إلزامي)
    SYSTEM_EMAIL: str
    SYSTEM_PASSWORD: str
    EMAIL_SERVER_HOST: str = "imap.gmail.com"
    SMTP_SERVER_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_TIMEOUT: int = 30
    EMAIL_RETRY_ATTEMPTS: int = 3
    EMAIL_RETRY_DELAY: int = 5

    # قاعدة البيانات
    DATABASE_URL: str = "sqlite:///jobs_system.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # الجدولة
    FETCH_INTERVAL_MINUTES: int = 30
    DISPATCH_INTERVAL_MINUTES: int = 15
    LOG_LEVEL: str = "INFO"

    # الأمان
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    PASSWORD_ALGORITHM: str = "bcrypt"
    PASSWORD_HASH_ROUNDS: int = 12

    # حدود التطبيق
    MAX_EMAIL_SIZE: int = 5_000_000  # 5MB
    MAX_JOB_LISTINGS_PER_FETCH: int = 100
    MAX_FAILED_ATTEMPTS_BEFORE_DISABLE: int = 5

    # المدول الدول والكلمات المفتاحية
    COUNTRIES_KEYWORDS: dict[str, list[str]] = {
        "Canada": ["canada", "toronto", "vancouver", "كندا"],
        "Germany": ["germany", "berlin", "hamburg", "ألمانيا"],
        "France": ["france", "paris", "فرنسا"],
        "UAE": ["uae", "dubai", "abu dhabi", "الإمارات"],
        "Qatar": ["qatar", "doha", "قطر"],
        "Saudi Arabia": ["saudi", "riyadh", "السعودية"],
        "UK": ["uk", "united kingdom", "london", "بريطانيا"],
        "USA": ["usa", "united states", "new york", "أمريكا"],
        "International": ["international", "global", "remote", "دولي"],
    }

    class Config:
        env_file = ".env"
        case_sensitive = True

    def model_post_init(self, __context: Any) -> None:
        """التحقق من القيم الحساسة"""
        if not self.SYSTEM_EMAIL or not self.SYSTEM_PASSWORD:
            raise ValueError(
                "❌ SYSTEM_EMAIL و SYSTEM_PASSWORD مطلوبة في ملف .env"
            )
        if self.JWT_SECRET_KEY == "your-secret-key-change-in-production":
            print(
                "⚠️  تحذير: استخدم JWT_SECRET_KEY مخصص في الإنتاج للأمان الأفضل"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """الحصول على الإعدادات المخزنة مؤقتاً"""
    return Settings()


settings = get_settings()
