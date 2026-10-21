"""Notification configuration. CONTACT_EMAIL_TO and RESEND_API_KEY come from Secret Manager
(bound in main.py); empty means "not configured" and the email is skipped with a warning.
Whitespace counts as empty: Secret Manager rejects an empty version, so a deploy without email
set up binds a single newline as the placeholder (.docs/RUNBOOK.md, Contact form keys)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class NotificationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", str_strip_whitespace=True)

    resend_api_key: str = ""
    contact_email_to: str = ""
    mail_from: str = "no-reply@nikunjramani.in"


@lru_cache
def get_notification_settings() -> NotificationSettings:
    return NotificationSettings()
