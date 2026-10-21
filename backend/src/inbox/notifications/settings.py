"""Notification configuration. CONTACT_EMAIL_TO and RESEND_API_KEY come from Secret Manager
(bound by `make deploy-api`); empty means "not configured" and the email is skipped with a
warning."""

from functools import lru_cache

from kernel.config import ServiceSettings


class NotificationSettings(ServiceSettings):
    required_in_production = ("mail_from",)

    resend_api_key: str = ""
    contact_email_to: str = ""
    mail_from: str = "no-reply@nikunjramani.in"


@lru_cache
def get_notification_settings() -> NotificationSettings:
    return NotificationSettings()
