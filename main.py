import time

from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import DISPATCH_INTERVAL_MINUTES, FETCH_INTERVAL_MINUTES
from database import db
from services.alert_dispatcher import AlertDispatcher
from services.email_receiver import EmailReceiver
from utils.logger import setup_logger

logger = setup_logger(__name__)


class JobAutomationSystem:
    def __init__(self):
        self.email_receiver = EmailReceiver()
        self.alert_dispatcher = AlertDispatcher()
        self.scheduler = BackgroundScheduler()

    def run_fetch_cycle(self):
        try:
            logger.info("بدء دورة جلب البريد")
            self.email_receiver.fetch_and_process()
        except Exception as exc:
            logger.exception(f"خطأ في جلب البريد: {exc}")

    def run_dispatch_cycle(self):
        try:
            logger.info("بدء دورة توزيع التنبيهات")
            self.alert_dispatcher.dispatch_alerts()
        except Exception as exc:
            logger.exception(f"خطأ في توزيع التنبيهات: {exc}")

    def start(self):
        try:
            self.run_fetch_cycle()
            self.run_dispatch_cycle()

            self.scheduler.add_job(self.run_fetch_cycle, "interval", minutes=FETCH_INTERVAL_MINUTES)
            self.scheduler.add_job(self.run_dispatch_cycle, "interval", minutes=DISPATCH_INTERVAL_MINUTES)
            self.scheduler.start()

            logger.info("تم بدء النظام بنجاح. اضغط Ctrl+C للإيقاف.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("إيقاف النظام...")
            self.scheduler.shutdown()
            db.engine.dispose()
        except Exception as exc:
            logger.exception(f"خطأ حرج: {exc}")
            self.scheduler.shutdown()
            db.engine.dispose()


if __name__ == "__main__":
    JobAutomationSystem().start()
