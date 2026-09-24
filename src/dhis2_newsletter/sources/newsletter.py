from __future__ import annotations

import email
import imaplib
import re
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import parsedate_to_datetime

from ..config import Secrets, SourceConfig
from ..models import Item

VIEW_IN_BROWSER_RE = re.compile(
    r'<a[^>]+href="([^"]+)"[^>]*>\s*View this email in your browser', re.IGNORECASE
)


def _decode(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    return "".join(
        p.decode(enc or "utf-8", errors="replace") if isinstance(p, bytes) else p
        for p, enc in parts
    )


def _get_part(msg: email.message.Message, content_type: str) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == content_type:
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    if msg.get_content_type() != content_type:
        return ""
    payload = msg.get_payload(decode=True)
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace") if payload else ""


def _view_in_browser_url(msg: email.message.Message) -> str:
    html = _get_part(msg, "text/html")
    match = VIEW_IN_BROWSER_RE.search(html)
    return match.group(1) if match else ""


def fetch(start: datetime, end: datetime, config: SourceConfig, secrets: Secrets) -> list[Item]:
    sender = config.model_extra.get("sender", "newsletter@dhis2.org")

    items: list[Item] = []
    M = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        M.login(secrets.smtp_user, secrets.smtp_password)
        M.select("INBOX", readonly=True)

        since = start.strftime("%d-%b-%Y")
        before = end.strftime("%d-%b-%Y")
        status, data = M.search(None, f'(FROM "{sender}" SINCE {since} BEFORE {before})')
        for msg_id in data[0].split():
            status, msg_data = M.fetch(msg_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            date = parsedate_to_datetime(msg["Date"])
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            if not (start <= date <= end):
                continue

            body = _get_part(msg, "text/plain").strip()
            items.append(
                Item(
                    source="newsletter",
                    title=_decode(msg["Subject"]),
                    url=_view_in_browser_url(msg),
                    published_at=date,
                    author=_decode(msg["From"]),
                    body=body[:5000],
                )
            )
    finally:
        M.logout()
    return items
