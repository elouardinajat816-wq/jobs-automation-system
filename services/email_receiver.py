import email
import imaplib
from email.header import decode_header

from bs4 import BeautifulSoup

from config.settings import EMAIL_SERVER_HOST, SYSTEM_EMAIL, SYSTEM_PASSWORD
from database import db, JobListing
from services.job_parser import JobParser
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EmailReceiver:
    def __init__(self):
        self.host = EMAIL_SERVER_HOST
        self.username = SYSTEM_EMAIL
        self.password = SYSTEM_PASSWORD

    def fetch_and_process(self):
        logger.info("[*] جاري فحص صندوق البريد عن عروض جديدة...")
        session = db.get_session()
        mail = None

        try:
            mail = imaplib.IMAP4_SSL(self.host)
            mail.login(self.username, self.password)
            mail.select("inbox")

            status, messages = mail.search(None, "UNSEEN")
            if status != "OK" or not messages[0]:
                logger.info("لا توجد رسائل جديدة.")
                return 0

            processed = 0
            for msg_id in messages[0].split():
                try:
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    for part in msg_data:
                        if isinstance(part, tuple):
                            msg = email.message_from_bytes(part[1])
                            subject = self.extract_subject(msg)
                            body = self.extract_body(msg)

                            if not subject or not body:
                                continue

                            job_data = JobParser.parse_job(subject, body)

                            existing = session.query(JobListing).filter_by(
                                title=job_data["title"],
                                country=job_data["country"],
                            ).first()

                            if existing:
                                logger.info(f"تم تخطي عرض مكرر: {subject}")
                                continue

                            job = JobListing(**{
                                "title": job_data["title"],
                                "country": job_data["country"],
                                "details": job_data["details"],
                                "contact_link": job_data["contact_link"],
                                "source_email": self.username,
                                "notified": False,
                            })
                            session.add(job)
                            session.commit()
                            processed += 1
                            logger.info(f"تم حفظ عرض جديد: {subject}")

                            mail.store(msg_id, "+FLAGS", "\\Seen")
                except Exception as exc:
                    logger.error(f"خطأ في معالجة رسالة: {exc}")
                    continue

            return processed

        except Exception as exc:
            logger.exception(f"خطأ أثناء جلب البريد: {exc}")
            return 0

        finally:
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass
            session.close()

    @staticmethod
    def extract_subject(msg) -> str | None:
        try:
            subject_header = msg.get("Subject", "No Subject")
            if not subject_header:
                return None

            decoded = decode_header(subject_header)
            subject = ""
            for item, encoding in decoded:
                if isinstance(item, bytes):
                    subject += item.decode(encoding or "utf-8", errors="ignore")
                else:
                    subject += str(item)

            return subject.strip() or None
        except Exception as exc:
            logger.warning(f"تعذر فك عنوان الرسالة: {exc}")
            return None

    @staticmethod
    def extract_body(msg) -> str | None:
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            return payload.decode(errors="ignore")
                    elif part.get_content_type() == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            html = payload.decode(errors="ignore")
                            soup = BeautifulSoup(html, "html.parser")
                            text = soup.get_text(" ", strip=True)
                            if text:
                                return text
                return None

            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode(errors="ignore")
            return None
        except Exception as exc:
            logger.warning(f"تعذر استخراج نص الرسالة: {exc}")
            return None
