from __future__ import annotations

from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest

from app.models import OAuthToken
from app.config import settings

def get_credentials(db: Session) -> Credentials:
    token = db.query(OAuthToken).filter(OAuthToken.provider == "google").first()
    if token is None:
        raise RuntimeError("Google is not connected. Visit /auth/google/login first.")

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri=token.token_uri,
        client_id=token.client_id,
        client_secret=token.client_secret,
        scopes=[s for s in (token.scopes or "").split(",") if s],
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        # Persist refreshed access token
        token.access_token = creds.token
        token.expiry = creds.expiry
        db.commit()

    return creds

def get_gmail_service(db: Session):
    creds = get_credentials(db)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def is_from_me(from_header: str | None) -> bool:
    if not from_header:
        return False
    fh = from_header.lower()
    for me in settings.my_emails_list():
        if me and me in fh:
            return True
    return False

def parse_email_address(from_header: str | None) -> tuple[str | None, str | None]:
    # Very small parser for "Name <email@x.com>" or "email@x.com"
    if not from_header:
        return None, None
    text = from_header.strip()
    if "<" in text and ">" in text:
        name = text.split("<")[0].strip().strip('"')
        email = text.split("<")[1].split(">")[0].strip()
        return (name or None), (email or None)
    return None, text
