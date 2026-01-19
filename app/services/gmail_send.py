from __future__ import annotations

import base64
from email.message import EmailMessage
from sqlalchemy.orm import Session

from app.services.gmail_client import get_gmail_service



def is_from_me(message: dict, me_email: str) -> bool:
    """
    Returns True if the message 'From' address matches the authenticated user's email.
    message: Gmail API message resource (or a dict with 'payload'->'headers').
    """
    try:
        headers = (message.get("payload") or {}).get("headers") or []
        from_val = next((h.get("value") for h in headers if (h.get("name") or "").lower() == "from"), "") or ""
        from_email = parseaddr(from_val)[1].lower().strip()
        return from_email == (me_email or "").lower().strip()
    except Exception:
        return False

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

from email.utils import parseaddr

