"""نسخة محسّنة من معالج الإرسال مع الأمان"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from config.settings import settings
from core.exceptions import EmailError, retry_on_exception, RetryConfig
from utils.logger import setup_logger

logger = setup_logger(__name__)

SMTP_RETRY_CONFIG = RetryConfig(
    max_attempts=settings.EMAIL_RETRY_ATTEMPTS,
    wait_base=settings.EMAIL_RETRY_DELAY,
)


class EmailSender:
    """معالج إرسال البريد مع معالجة الأخطاء"""

    def __init__(
        self,
        smtp_host: str = settings.SMTP_SERVER_HOST,
        smtp_port: int = settings.SMTP_PORT,
        from_email: str = settings.SYSTEM_EMAIL,
        password: str = settings.SYSTEM_PASSWORD,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.password = password

    @retry_on_exception(
        config=SMTP_RETRY_CONFIG,
        exceptions=(smtplib.SMTPException, ConnectionError, TimeoutError),
    )
    def send_job_alert(
        self,
        to_email: str,
        title: str,
        country: str,
        details: str,
        link: str | None,
    ) -> bool:
        """إرسال تنبيه وظيفة مع معالجة الأخطاء"""
        try:
            # التحقق من صحة البيانات
            title = escape(title)  # منع XSS
            details = escape(details)
            country = escape(country)

            msg = self._create_message(to_email, title, country, details, link)
            self._send_smtp(msg, to_email)
            logger.info(f"✅ تم إرسال البريد لـ: {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(f"❌ خطأ في المصادقة SMTP")
            raise EmailError("فشل التحقق من بيانات SMTP", "SMTP_AUTH_ERROR")
        except smtplib.SMTPException as e:
            logger.error(f"❌ خطأ SMTP: {e}")
            raise EmailError(f"خطأ في إرسال البريد: {str(e)}", "SMTP_ERROR")
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع: {e}")
            raise EmailError(f"خطأ في إرسال البريد: {str(e)}", "SEND_ERROR")

    def _create_message(
        self,
        to_email: str,
        title: str,
        country: str,
        details: str,
        link: str | None,
    ) -> MIMEMultipart:
        """إنشاء رسالة بريد احترافية"""
        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = f"🔥 فرصة عمل جديدة في {country}: {title}"

        text_body = self._create_text_body(title, country, details, link)
        html_body = self._create_html_body(title, country, details, link)

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        return msg

    @staticmethod
    def _create_text_body(
        title: str,
        country: str,
        details: str,
        link: str | None,
    ) -> str:
        """إنشاء نسخة نصية آمنة من الرسالة"""
        return f"""
مرحباً،

وصلت فرصة عمل جديدة تتطابق مع اهتمامك:

📌 المسمى: {title}
🌍 الدولة: {country}
📄 التفاصيل: {details}

🔗 رابط التقديم: {link if link else 'غير متوفر'}

---
تم إرسال هذا التنبيه تلقائياً من نظام المراقبة.
"""

    @staticmethod
    def _create_html_body(
        title: str,
        country: str,
        details: str,
        link: str | None,
    ) -> str:
        """إنشاء نسخة HTML آمنة من الرسالة مع منع XSS"""
        link_html = (
            f'<a href="{escape(link)}" style="background: #0d6efd; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none;">التقديم الآن</a>'
            if link
            else '<p style="color: #666;">الرابط غير متوفر</p>'
        )

        return f"""
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; direction: rtl; background-color: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 600px; margin: auto; background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background-color: #0d6efd; color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }}
        .content {{ color: #333; }}
        .job-info {{ background-color: #f9f9f9; padding: 15px; border-right: 4px solid #0d6efd; margin: 15px 0; }}
        .job-info p {{ margin: 8px 0; }}
        .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h2>🔥 فرصة عمل جديدة</h2>
    </div>
    <div class="content">
        <p>مرحباً،</p>
        <p>وصلت فرصة عمل جديدة تتطابق مع اهتمامك:</p>
        <div class="job-info">
            <p><strong>📌 المسمى:</strong> {escape(title)}</p>
            <p><strong>🌍 الدولة:</strong> {escape(country)}</p>
            <p><strong>📄 التفاصيل:</strong> {escape(details[:200])}</p>
            {link_html}
        </div>
    </div>
    <div class="footer">
        <p>تم إرسال هذا التنبيه تلقائياً من نظام مراقبة فرص العمل</p>
    </div>
</div>
</body>
</html>
"""

    def _send_smtp(self, msg: MIMEMultipart, to_email: str) -> None:
        """إرسال البريد عبر SMTP مع معالجة الأخطاء"""
        server = None
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=settings.EMAIL_TIMEOUT)
            server.starttls()
            server.login(self.from_email, self.password)
            server.sendmail(self.from_email, to_email, msg.as_string())
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
