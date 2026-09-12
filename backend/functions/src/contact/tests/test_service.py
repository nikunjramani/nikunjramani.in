"""Unit tests for ContactService, with the repository and rate limiter faked.

The point of these is the *disguise* behaviour — a honeypot trip, a rate limit, and a
failed Turnstile check must all look identical to success from the caller's side. If any
of them raised or the repository still got a create() call, that would be the actual
security property breaking silently. See src/contact/service.py.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from shared.core.errors import RateLimitedError
from src.contact.service import ContactService


@pytest.fixture
def service_with_fakes() -> tuple[ContactService, MagicMock, MagicMock]:
    svc = ContactService.__new__(ContactService)  # skip __init__'s real Firestore client
    repo = MagicMock()
    limiter = MagicMock()
    svc._repo = repo
    svc._limiter = limiter
    return svc, repo, limiter


def _submit(svc: ContactService, **overrides: Any) -> None:
    defaults: dict[str, Any] = {
        "name": "A Visitor",
        "email": "visitor@example.com",
        "message": "Hello there, loved the site.",
        "ip": "1.2.3.4",
        "user_agent": "pytest",
    }
    defaults.update(overrides)
    svc.submit(**defaults)


def test_honeypot_trip_is_silently_discarded(
    service_with_fakes: tuple[ContactService, MagicMock, MagicMock],
) -> None:
    svc, repo, limiter = service_with_fakes
    _submit(svc, honeypot="i-am-a-bot")
    repo.create.assert_not_called()
    limiter.check.assert_not_called()  # never even reaches the rate limiter


def test_rate_limited_is_silently_discarded(
    service_with_fakes: tuple[ContactService, MagicMock, MagicMock],
) -> None:
    svc, repo, limiter = service_with_fakes
    limiter.check.side_effect = RateLimitedError("too many")
    _submit(svc)
    repo.create.assert_not_called()


def test_failed_turnstile_is_silently_discarded(
    service_with_fakes: tuple[ContactService, MagicMock, MagicMock],
) -> None:
    svc, repo, _limiter = service_with_fakes
    with patch("src.contact.service.verify_turnstile", return_value=False):
        _submit(svc)
    repo.create.assert_not_called()


def test_legitimate_submission_is_persisted(
    service_with_fakes: tuple[ContactService, MagicMock, MagicMock],
) -> None:
    svc, repo, _limiter = service_with_fakes
    with patch("src.contact.service.verify_turnstile", return_value=True):
        _submit(svc, message="A perfectly normal message.")
    repo.create.assert_called_once()
    entry = repo.create.call_args.args[0]
    assert entry.name == "A Visitor"
    assert entry.spamScore == 0.0


def test_spammy_message_is_persisted_but_flagged_not_blocked(
    service_with_fakes: tuple[ContactService, MagicMock, MagicMock],
) -> None:
    svc, repo, _limiter = service_with_fakes
    spammy = "https://a.com https://b.com https://c.com BUY NOW BUY NOW BUY NOW"
    with patch("src.contact.service.verify_turnstile", return_value=True):
        _submit(svc, message=spammy)
    repo.create.assert_called_once()
    entry = repo.create.call_args.args[0]
    assert entry.spamScore > 0.5  # flagged
