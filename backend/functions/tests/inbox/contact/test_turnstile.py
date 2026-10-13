from __future__ import annotations

from unittest.mock import patch

import pytest

from kernel.config import Settings
from src.inbox.contact.settings import ContactSettings
from src.inbox.contact.turnstile import verify_turnstile


@pytest.mark.parametrize(
    ("environment", "expected"), [("production", False), ("development", True)]
)
def test_missing_secret_fails_closed_only_in_production(environment: str, expected: bool) -> None:
    settings = Settings(environment=environment)  # type: ignore[arg-type]
    with (
        patch("src.inbox.contact.turnstile.get_settings", return_value=settings),
        patch(
            "src.inbox.contact.turnstile.get_contact_settings",
            return_value=ContactSettings(turnstile_secret_key=""),
        ),
    ):
        assert verify_turnstile("", remote_ip="1.2.3.4") is expected


def test_empty_token_is_rejected_when_a_secret_is_configured() -> None:
    with (
        patch(
            "src.inbox.contact.turnstile.get_settings",
            return_value=Settings(environment="production"),
        ),
        patch(
            "src.inbox.contact.turnstile.get_contact_settings",
            return_value=ContactSettings(turnstile_secret_key="secret"),
        ),
    ):
        assert verify_turnstile("", remote_ip="1.2.3.4") is False
