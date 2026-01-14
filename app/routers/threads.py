from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from googleapiclient.errors import HttpError

from app.db import get_db
from app.services.gmail_client import get_gmail_service  # your existing service builder
from app.services.gmail_parse import extract_message_body

router = APIRouter()

@router.get("/tickets/{thread_id}/thread")
def get_thread(thread_id: str, db: Session = Depends(get_db)):
    service = get_gmail_service(db)

    try:
        thread = service.users().threads().get(
            userId="me",
            id=thread_id,
            format="full",
        ).execute()
    except HttpError as e:
        raise HTTPException(status_code=400, detail=str(e))

    messages_out = []
    for m in thread.get("messages", []) or []:
        payload = m.get("payload", {}) or {}
        headers = {h["name"].lower(): h["value"] for h in (payload.get("headers", []) or []) if "name" in h and "value" in h}

        body_info = extract_message_body(payload)

        messages_out.append({
            "id": m.get("id"),
            "thread_id": m.get("threadId"),
            "internal_date": m.get("internalDate"),
            "from": headers.get("from"),
            "to": headers.get("to"),
            "subject": headers.get("subject"),
            "date": headers.get("date"),
            "snippet": m.get("snippet"),
            "body_text": body_info["body_text"],
            "used_mime": body_info["used_mime"],
            # Optional: include HTML if you want a "View HTML" toggle in UI
            # "body_html": body_info["body_html"],
        })

    return {
        "thread_id": thread_id,
        "messages": messages_out,
        "gmail_thread_url": f"https://mail.google.com/mail/u/0/#inbox/{thread_id}",
    }
