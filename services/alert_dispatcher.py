import time

from database import db, EmailLog, JobListing, Subscriber
from services.email_sender import EmailSender
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AlertDispatcher:
    def __init__(self):
        self.sender = EmailSender()

    def dispatch_alerts(self):
        logger.info("[*] جاري فحص العروض غير المرسلة...")
        session = db.get_session()

        try:
            new_jobs = session.query(JobListing).filter_by(notified=False).all()
            if not new_jobs:
                logger.info("لا توجد عروض جديدة لتنبيه المشتركين.")
                return 0

            total_sent = 0
            for job in new_jobs:
                subscribers = session.query(Subscriber).filter(
                    (Subscriber.preferred_country == job.country) | (Subscriber.preferred_country == "International"),
                    Subscriber.active == True,
                ).all()

                if not subscribers:
                    logger.info(f"لا يوجد مشتركين مهتمين بـ {job.country}")
                    job.notified = True
                    session.commit()
                    continue

                for sub in subscribers:
                    success = self.sender.send_job_alert(
                        to_email=sub.email,
                        title=job.title,
                        country=job.country,
                        details=job.details,
                        link=job.contact_link,
                    )

                    session.add(EmailLog(
                        recipient=sub.email,
                        job_id=job.id,
                        status="success" if success else "failed",
                        error_message=None if success else "فشل في إرسال البريد",
                    ))
                    if success:
                        total_sent += 1
                    time.sleep(0.4)

                job.notified = True
                job.processed_at = __import__('datetime').datetime.utcnow()
                session.commit()
                logger.info(f"[✓] تم الانتهاء من معالجة العرض رقم: {job.id}")

            return total_sent

        except Exception as exc:
            logger.exception(f"خطأ أثناء توزيع التنبيهات: {exc}")
            return 0
        finally:
            session.close()
