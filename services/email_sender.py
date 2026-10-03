import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import SMTP_PORT, SMTP_SERVER_HOST, SYSTEM_EMAIL, SYSTEM_PASSWORD
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EmailSender:
    def __init__(self):
        self.smtp_host = SMTP_SERVER_HOST
        self.smtp_port = SMTP_PORT
        self.from_email = SYSTEM_EMAIL
        self.password = SYSTEM_PASSWORD

    def send_job_alert(self, to_email: str, title: str, country: str, details: str, link: str | None):
        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = f"🔥 فرصة عمل جديدة في {country}: {title}"

        text_body = f"""
مرحباً،

وصلت فرصة عمل جديدة تتوافق مع اهتمامتك:

📌 المسمى: {title}
🌍 الدولة: {country}
📄 التفاصيل: {details}

🔗 رابط التقديم: {link if link else 'غير متوفر'}

---
تم إرسال هذا التنبيه تلقائياً من نظام التوظيف.
"""

        html_body = f"""
<html>
<body style='font-family: Arial, sans-serif; direction: rtl; background-color: #f5f5f5; padding: 20px;'>
<div style='max-width: 600px; margin: auto; background: white; border-radius: 12px; padding: 20px;'>
    <h2 style='color: #0d6efd;'>🔥 فرصة عمل جديدة</h2>
    <p><strong>المسمى:</strong> {title}</p>
    <p><strong>الدولة:</strong> {country}</p>
    <p><strong>التفاصيل:</strong> {details}</p>
    <p><a href='{link if link else "#"}' style='background: #0d6efd; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none;'>التقديم الآن</a></p>
</div>
</body>
</html>
"""

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.password)
            server.sendmail(self.from_email, to_email, msg.as_string())
            server.quit()
            logger.info(f"تم إرسال الإشعار إلى: {to_email}")
            return True
        except Exception as exc:
            logger.exception(f"فشل إرسال الإشعار إلى {to_email}: {exc}")
            return False
