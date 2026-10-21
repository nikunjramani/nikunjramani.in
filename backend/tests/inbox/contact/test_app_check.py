from __future__ import annotations

from unittest.mock import patch

import pytest

from kernel.config import Settings
from src.inbox.contact.app_check import verify_app_check

PROD = Settings(environment="production", service_url="https://api-1.asia-south1.run.app")
DEV = Settings(environment="development")


@pytest.mark.parametrize(("settings", "expected"), [(PROD, False), (DEV, True)])
def test_missing_token_fails_closed_only_in_production(settings: Settings, expected: bool) -> None:
    with (
        patch("src.inbox.contact.app_check.get_settings", return_value=settings),
        patch("src.inbox.contact.app_check.app_check.verify_token") as verify,
    ):
        assert verify_app_check("") is expected
    verify.assert_not_called()


def test_valid_token_is_accepted() -> None:
    with (
        patch("src.inbox.contact.app_check.get_settings", return_value=PROD),
        patch("src.inbox.contact.app_check.ensure_app"),
        patch("src.inbox.contact.app_check.app_check.verify_token", return_value={"sub": "app"}),
    ):
        assert verify_app_check("a-token") is True


@pytest.mark.parametrize("error", [ValueError("bad token"), RuntimeError("JWKS unreachable")])
def test_any_verification_error_fails_closed(error: Exception) -> None:
    with (
        patch("src.inbox.contact.app_check.get_settings", return_value=PROD),
        patch("src.inbox.contact.app_check.ensure_app"),
        patch("src.inbox.contact.app_check.app_check.verify_token", side_effect=error),
    ):
        assert verify_app_check("a-token") is False
