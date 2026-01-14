from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from app.config import settings
from app.db import get_db
from app.models import OAuthToken

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
]

def _flow() -> Flow:
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_OAUTH_CLIENT_FILE,
        scopes=SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow

@router.get("/google/login")
def google_login():
    flow = _flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(auth_url)

@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    flow = _flow()
    flow.fetch_token(code=code)

    creds: Credentials = flow.credentials

    # Upsert single token row
    token = db.query(OAuthToken).filter(OAuthToken.provider == "google").first()
    scopes_csv = ",".join(creds.scopes or [])

    if token is None:
        token = OAuthToken(
            provider="google",
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_uri=creds.token_uri,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            scopes=scopes_csv,
            expiry=creds.expiry,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(token)
    else:
        token.access_token = creds.token
        # refresh_token may be None on subsequent auths; keep existing if missing
        if creds.refresh_token:
            token.refresh_token = creds.refresh_token
        token.token_uri = creds.token_uri
        token.client_id = creds.client_id
        token.client_secret = creds.client_secret
        token.scopes = scopes_csv
        token.expiry = creds.expiry
        token.updated_at = datetime.utcnow()

    db.commit()

    return JSONResponse({"ok": True, "message": "Google account connected. You can now sync inbox."})