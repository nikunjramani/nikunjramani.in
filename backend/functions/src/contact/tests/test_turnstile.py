from __future__ import annotations

from unittest.mock import patch

import pytest

from shared.core.config import Settings
from src.contact.turnstile import verify_turnstile


@pytest.mark.parametrize(
    ("environment", "expected"), [("production", False), ("development", True)]
)
def test_missing_secret_fails_closed_only_in_production(environment: str, expected: bool) -> None:
    settings = Settings(environment=environment, turnstile_secret_key="")  # type: ignore[arg-type]
    with patch("src.contact.turnstile.get_settings", return_value=settings):
        assert verify_turnstile("", remote_ip="1.2.3.4") is expected


def test_empty_token_is_rejected_when_a_secret_is_configured() -> None:
    settings = Settings(environment="production", turnstile_secret_key="secret")
    with patch("src.contact.turnstile.get_settings", return_value=settings):
        assert verify_turnstile("", remote_ip="1.2.3.4") is False
