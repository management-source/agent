from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from app.config import settings
from app.models import OAuthToken
from sqlalchemy.orm import Session
from email.utils import parseaddr

def get_gmail_service(db: Session):
    token = db.query(OAuthToken).filter(OAuthToken.provider == "google").first()
    if not token:
        raise RuntimeError("Google not connected. Please login again.")

    scopes = [s for s in (token.scopes or "").split(",") if s]

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri=token.token_uri or "https://oauth2.googleapis.com/token",
        # CRITICAL: use env vars (not DB) after JSON removal
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=scopes,
    )

    # Refresh if needed
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        token.access_token = creds.token
        token.expiry = creds.expiry
        db.commit()

    return build("gmail", "v1", credentials=creds, cache_discovery=False)

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
