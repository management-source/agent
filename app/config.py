from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./email_autopilot.db"

    GOOGLE_OAUTH_CLIENT_FILE: str
    GOOGLE_REDIRECT_URI: str

    MY_EMAILS: str = ""
    POLL_INTERVAL_SECONDS: int = 300
    REMINDER_INTERVAL_SECONDS: int = 900
    REMINDER_COOLDOWN_SECONDS: int = 3600
    REMINDER_TO_EMAIL: str | None = None

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    class Config:
        extra = "ignore"


settings = Settings()
