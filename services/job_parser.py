"""استخلاص قابل للتطوير ومرن"""
import re
from typing import Optional

from schemas import JobListingCreate
from config.settings import settings
from utils.validators import clean_text, extract_urls
from utils.logger import setup_logger

logger = setup_logger(__name__)


class JobParser:
    """محلل عروض العمل مع معالجة قوية للأخطاء"""

    # نماذج Regex قابلة للتطوير
    SALARY_PATTERNS = [
        r"\$?\d+[,.]?\d*[Kk]?\s*(?:-|to|–)\s*\$?\d+[,.]?\d*[Kk]?",
        r"(?:salary|salary range|compensation):\s*[^\n]*",
    ]

    DEADLINE_PATTERNS = [
        r"(?:deadline|apply by|closes on):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(?:closes|deadline)\s+(?:on|at)?\s*([^\n]+)",
    ]

    @staticmethod
    def parse_job(subject: str, body: str) -> JobListingCreate:
        """تحليل البريد واستخراج بيانات الوظيفة"""
        try:
            title = JobParser._extract_title(subject)
            country = JobParser._detect_country(subject, body)
            details = JobParser._extract_details(body)
            link = JobParser._extract_link(body)

            return JobListingCreate(
                title=title or "وظيفة بدون عنوان",
                country=country,
                details=details or "تفاصيل الوظيفة متاحة في الرابط المرفق",
                contact_link=link,
            )
        except Exception as e:
            logger.error(f"خطأ في تحليل الوظيفة: {e}")
            raise

    @staticmethod
    def _extract_title(subject: str) -> Optional[str]:
        """استخراج عنوان الوظيفة مع التحقق من الصحة"""
        if not subject:
            return None

        # إزالة البادئات الشائعة
        cleaned = re.sub(
            r"^(Re:|Fwd:|FW:|RE:|\[|\*)",
            "",
            subject,
            flags=re.IGNORECASE,
        ).strip()

        # الحد الأدنى 3 أحرف والحد الأقصى 255
        if len(cleaned) < 3:
            return None

        return cleaned[:255]

    @staticmethod
    def _detect_country(subject: str, body: str) -> str:
        """كشف الدولة من محتوى البريد"""
        combined = (subject + " " + body).lower()

        # البحث في الكلمات المفتاحية
        for country, keywords in settings.COUNTRIES_KEYWORDS.items():
            if country == "International":
                continue
            for keyword in keywords:
                if keyword.lower() in combined:
                    logger.debug(f"🌍 تم كشف الدولة: {country}")
                    return country

        return "International"

    @staticmethod
    def _extract_details(body: str) -> Optional[str]:
        """استخراج ملخص التفاصيل بشكل ذكي"""
        if not body:
            return None

        # استخراج المراحل الأولى قبل الأسطر الفارغة
        lines = body.split("\n")
        details = []

        for line in lines[:20]:
            stripped = line.strip()
            if len(stripped) > 3:
                details.append(stripped)
            if len("\n".join(details)) > 500:
                break

        text = "\n".join(details)
        text = clean_text(text)

        return text[:500] if text else None

    @staticmethod
    def _extract_link(body: str) -> Optional[str]:
        """استخراج رابط التقديم بأولوية"""
        if not body:
            return None

        urls = extract_urls(body)

        # الأولوية للروابط التي تحتوي على كلمات معينة
        priority_keywords = ["apply", "job", "career", "recruit", "التقديم", "الوظيفة"]
        for url in urls:
            if any(keyword in url.lower() for keyword in priority_keywords):
                return url

        # إذا لم نجد رابط بأولوية، نأخذ الأول
        return urls[0] if urls else None

    @staticmethod
    def extract_salary(body: str) -> Optional[str]:
        """استخراج معلومات الراتب إن وجدت"""
        for pattern in JobParser.SALARY_PATTERNS:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def extract_deadline(body: str) -> Optional[str]:
        """استخراج موعد انتهاء التقديم إن وجد"""
        for pattern in JobParser.DEADLINE_PATTERNS:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None
