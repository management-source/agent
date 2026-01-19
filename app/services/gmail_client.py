from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from app.config import settings
from app.models import OAuthToken
from sqlalchemy.orm import Session

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
