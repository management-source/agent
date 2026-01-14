from fastapi import APIRouter, Depends, HTTPException, Request
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
    # Must be the Cloud Run https URL in production
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow

@router.get("/google/login")
def google_login():
    if not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="GOOGLE_REDIRECT_URI not configured")

    flow = _flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    # state is generated for CSRF protection; you can store it in a cookie/session later if desired
    return RedirectResponse(auth_url)

@router.get("/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db)):
    # Google can return ?error=access_denied etc.
    err = request.query_params.get("error")
    if err:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {err}")

    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    flow = _flow()

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        # This is where redirect_uri_mismatch usually surfaces
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {repr(e)}")

    creds: Credentials = flow.credentials

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
        # IMPORTANT: do NOT overwrite refresh token with None
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
