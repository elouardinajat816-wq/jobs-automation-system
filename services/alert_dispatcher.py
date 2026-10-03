"""خدمة توزيع التنبيهات المحسّنة"""
import time
from typing import Optional

from database import db
from crud import SubscriberCRUD, JobListingCRUD, EmailLogCRUD
from core.exceptions import ApplicationError
from services.email_sender import EmailSender
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AlertDispatcher:
    """موزع التنبيهات مع معالجة قوية للأخطاء"""

    def __init__(self):
        self.sender = EmailSender()

    def dispatch_alerts(self) -> int:
        """توزيع التنبيهات على المشتركين المهتمين"""
        logger.info("🔔 بدء دورة توزيع التنبيهات")
        session = db.get_session()
        total_sent = 0

        try:
            # جلب العروض الجديدة
            new_jobs = JobListingCRUD.get_unnotified(
                session, 
                limit=100
            )
            if not new_jobs:
                logger.info("ℹ️ لا توجد عروض جديدة للإرسال")
                return 0

            logger.info(f"📢 تم العثور على {len(new_jobs)} عرض جديد")

            for job in new_jobs:
                try:
                    sent = self._process_job(session, job)
                    total_sent += sent

                    # تحديث حالة العرض
                    JobListingCRUD.mark_notified(session, job.id)
                    logger.info(f"✅ تم الانتهاء من العرض {job.id}")

                except ApplicationError as e:
                    logger.error(f"❌ خطأ في معالجة العرض {job.id}: {e.message}")
                    continue
                except Exception as e:
                    logger.exception(f"❌ خطأ غير متوقع في معالجة العرض {job.id}: {e}")
                    continue

            logger.info(f"🎉 تم إرسال {total_sent} تنبيه بنجاح")
            return total_sent

        except Exception as e:
            logger.exception(f"❌ خطأ في دورة التوزيع: {e}")
            return 0
        finally:
            session.close()

    def _process_job(self, session, job) -> int:
        """معالجة عرض واحد وإرسال التنبيهات"""
        # جلب المشتركين المهتمين
        subscribers = SubscriberCRUD.get_by_country(session, job.country)

        if not subscribers:
            logger.info(f"ℹ️ لا يوجد مشتركين مهتمين بـ {job.country}")
            return 0

        logger.info(f"📧 إرسال التنبيه لـ {len(subscribers)} مشترك")

        sent_count = 0
        for sub in subscribers:
            success = self._send_to_subscriber(session, sub, job)
            if success:
                sent_count += 1
            time.sleep(0.3)  # تأخير صغير

        return sent_count

    def _send_to_subscriber(self, session, subscriber, job) -> bool:
        """إرسال البريد للمشترك الواحد"""
        try:
            # محاولة الإرسال
            success = self.sender.send_job_alert(
                to_email=subscriber.email,
                title=job.title,
                country=job.country,
                details=job.details,
                link=job.contact_link,
            )

            # تسجيل النتيجة
            EmailLogCRUD.create(
                session,
                recipient=subscriber.email,
                job_id=job.id,
                status="success" if success else "failed",
            )

            return success

        except Exception as e:
            logger.error(f"❌ فشل إرسال البريد لـ {subscriber.email}: {e}")
            EmailLogCRUD.create(
                session,
                recipient=subscriber.email,
                job_id=job.id,
                status="failed",
                error_message=str(e),
            )
            return False
