from __future__ import annotations
from email.utils import parseaddr
import base64
from email.message import EmailMessage
from sqlalchemy.orm import Session

from app.services.gmail_client import get_gmail_service

def send_reply_in_thread(
    db: Session,
    thread_id: str,
    to_email: str | None,
    subject: str,
    body: str,
):
    if not to_email:
        raise ValueError("Missing recipient email")

    service = get_gmail_service(db)

    msg = EmailMessage()
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    service.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": thread_id},
    ).execute()



def is_from_me(message: dict, me_email: str) -> bool:
    """
    True if the Gmail message 'From' address equals the authenticated user's email.

    message: Gmail API message dict (expects payload.headers).
    me_email: The authenticated user's primary email address.
    """
    try:
        headers = (message.get("payload") or {}).get("headers") or []
        from_value = next(
            (h.get("value") for h in headers if (h.get("name") or "").lower() == "from"),
            "",
        ) or ""
        from_email = parseaddr(from_value)[1].lower().strip()
        return from_email == (me_email or "").lower().strip()
    except Exception:
        return False

