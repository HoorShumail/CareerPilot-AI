import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.config.settings import settings
from src.config.logging import logger


class EmailSender:
    def __init__(self):
        self.enabled = settings.EMAILS_ENABLED
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.starttls = settings.SMTP_STARTTLS
        self.from_email = settings.EMAILS_FROM

    def send_email(self, to_email: str, subject: str, body: str) -> None:
        if not self.enabled:
            logger.info("Email sending is disabled; skipping send to %s", to_email)
            return

        if not self.smtp_host or not self.smtp_user or not self.smtp_password:
            raise ValueError("SMTP settings are incomplete. Cannot send email.")

        message = MIMEMultipart()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.starttls:
                server.starttls(context=context)
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, to_email, message.as_string())
