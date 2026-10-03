"""نسخة محسّنة من معالج البريد مع الأمان والتحمل"""
import email
import imaplib
import time
from email.header import decode_header
from typing import Optional

from bs4 import BeautifulSoup

from config.settings import settings
from core.exceptions import EmailError, retry_on_exception, RetryConfig
from database import db, JobListing
from crud import JobListingCRUD
from services.job_parser import JobParser
from utils.logger import setup_logger

logger = setup_logger(__name__)

EMAIL_RETRY_CONFIG = RetryConfig(
    max_attempts=settings.EMAIL_RETRY_ATTEMPTS,
    wait_base=settings.EMAIL_RETRY_DELAY,
)


class EmailReceiver:
    """معالج استقبال البريد مع معالجة متقدمة للأخطاء"""

    def __init__(
        self,
        host: str = settings.EMAIL_SERVER_HOST,
        username: str = settings.SYSTEM_EMAIL,
        password: str = settings.SYSTEM_PASSWORD,
        timeout: int = settings.EMAIL_TIMEOUT,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.mail: Optional[imaplib.IMAP4_SSL] = None

    @retry_on_exception(
        config=EMAIL_RETRY_CONFIG,
        exceptions=(imaplib.IMAP4.error, ConnectionError, TimeoutError),
    )
    def _connect(self) -> imaplib.IMAP4_SSL:
        """الاتصال بخادم IMAP مع الإعادة التلقائية"""
        try:
            logger.info(f"محاولة الاتصال بـ {self.host}...")
            mail = imaplib.IMAP4_SSL(self.host, timeout=self.timeout)
            mail.login(self.username, self.password)
            logger.info(f"✅ تم الاتصال بنجاح بـ {self.host}")
            return mail
        except imaplib.IMAP4.error as e:
            logger.error(f"❌ خطأ في المصادقة: {e}")
            raise EmailError(f"فشل الاتصال بخادم البريد: {str(e)}", "AUTH_ERROR")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"❌ خطأ في الاتصال: {e}")
            raise EmailError(f"خطأ في الاتصال بالخادم: {str(e)}", "CONNECTION_ERROR")

    def _disconnect(self) -> None:
        """قطع الاتصال بشكل آمن"""
        try:
            if self.mail:
                self.mail.logout()
                logger.info("تم قطع الاتصال بنجاح")
        except Exception as e:
            logger.warning(f"خطأ في قطع الاتصال: {e}")

    def _extract_subject(self, msg: email.message.Message) -> Optional[str]:
        """استخراج عنوان البريد بشكل آمن"""
        try:
            subject_header = msg.get("Subject", "")
            if not subject_header:
                return None

            decoded = decode_header(subject_header)
            subject = ""

            for part, encoding in decoded:
                if isinstance(part, bytes):
                    subject += part.decode(encoding or "utf-8", errors="ignore")
                else:
                    subject += str(part) if part else ""

            return subject.strip() or None
        except Exception as e:
            logger.warning(f"خطأ في استخراج العنوان: {e}")
            return None

    def _extract_body(self, msg: email.message.Message) -> Optional[str]:
        """استخراج محتوى البريد بشكل آمن"""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    payload = part.get_payload(decode=True)

                    if not payload:
                        continue

                    if content_type == "text/plain":
                        return payload.decode(errors="ignore")
                    elif content_type == "text/html":
                        html_content = payload.decode(errors="ignore")
                        soup = BeautifulSoup(html_content, "html.parser")
                        text = soup.get_text(" ", strip=True)
                        return text if text else None

                return None

            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode(errors="ignore")
            return None
        except Exception as e:
            logger.warning(f"خطأ في استخراج المحتوى: {e}")
            return None

    def fetch_and_process(self) -> int:
        """جلب ومعالجة الرسائل الجديدة"""
        logger.info("🔍 بدء فحص صندوق البريد...")
        session = db.get_session()
        processed_count = 0

        try:
            self.mail = self._connect()
            self.mail.select("inbox")

            status, messages = self.mail.search(None, "UNSEEN")
            if status != "OK" or not messages[0]:
                logger.info("ℹ️ لم يتم العثور على رسائل جديدة")
                return 0

            message_ids = messages[0].split()
            logger.info(f"📧 عدد الرسائل الجديدة: {len(message_ids)}")

            for msg_id in message_ids[:settings.MAX_JOB_LISTINGS_PER_FETCH]:
                try:
                    res, msg_data = self.mail.fetch(msg_id, "(RFC822)")
                    if res != "OK":
                        continue

                    for part in msg_data:
                        if not isinstance(part, tuple):
                            continue

                        msg = email.message_from_bytes(part[1])
                        subject = self._extract_subject(msg)
                        body = self._extract_body(msg)

                        if not subject or not body:
                            logger.debug("تم تخطي رسالة بدون عنوان أو محتوى")
                            continue

                        # تحليل البيانات
                        job_data = JobParser.parse_job(subject, body)

                        # التحقق من التكرار
                        if JobListingCRUD.check_duplicate(
                            session,
                            job_data.title,
                            job_data.country,
                        ):
                            logger.debug(f"تم تخطي عرض مكرر: {subject}")
                            continue

                        # حفظ في قاعدة البيانات
                        job = JobListingCRUD.create(session, job_data)
                        processed_count += 1
                        logger.info(f"✅ تم حفظ عرض جديد: {job.title}")

                        # تحديد كمقروء
                        self.mail.store(msg_id, "+FLAGS", "\\Seen")

                except Exception as e:
                    logger.error(f"❌ خطأ في معالجة الرسالة: {e}")
                    continue

            logger.info(f"🎉 تم معالجة {processed_count} عرض جديد")
            return processed_count

        except EmailError as e:
            logger.error(f"❌ خطأ في البريد: {e.message}")
            return 0
        except Exception as e:
            logger.exception(f"❌ خطأ غير متوقع: {e}")
            return 0
        finally:
            self._disconnect()
            session.close()
