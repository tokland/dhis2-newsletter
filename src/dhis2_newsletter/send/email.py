from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import Secrets


def send_email(
    subject: str,
    html_body: str,
    plain_body: str,
    recipients: list[str],
    secrets: Secrets,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = secrets.smtp_user
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(secrets.smtp_host, secrets.smtp_port) as server:
        server.starttls()
        server.login(secrets.smtp_user, secrets.smtp_password)
        server.sendmail(secrets.smtp_user, recipients, msg.as_string())
