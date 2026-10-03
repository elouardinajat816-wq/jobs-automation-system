import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_EMAIL = os.getenv("SYSTEM_EMAIL")
SYSTEM_PASSWORD = os.getenv("SYSTEM_PASSWORD")
EMAIL_SERVER_HOST = os.getenv("EMAIL_SERVER_HOST", "imap.gmail.com")
SMTP_SERVER_HOST = os.getenv("SMTP_SERVER_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///jobs_system.db")
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))
DISPATCH_INTERVAL_MINUTES = int(os.getenv("DISPATCH_INTERVAL_MINUTES", "15"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

COUNTRIES_KEYWORDS = {
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

if not SYSTEM_EMAIL or not SYSTEM_PASSWORD:
    raise ValueError("SYSTEM_EMAIL و SYSTEM_PASSWORD يجب أن تكونا موجودتين في ملف .env")
