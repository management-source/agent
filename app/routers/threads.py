from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ThreadTicket
from app.services.gmail_threads import get_thread_details

router = APIRouter()

@router.get("/{thread_id}")
def thread_details(thread_id: str, db: Session = Depends(get_db)):
    t = db.get(ThreadTicket, thread_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return get_thread_details(db=db, thread_id=thread_id)
