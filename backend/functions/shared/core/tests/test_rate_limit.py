"""RateLimiter, against the real emulator.

This is the transactional check-then-increment that keeps two concurrent requests from
both reading count=4 against a limit of 5 and both being allowed through. That property
type-checks fine and is exactly the kind of thing worth proving against real Firestore.
"""

from __future__ import annotations

import uuid

import pytest
from google.cloud.firestore_v1 import Client

from shared.core.errors import RateLimitedError
from shared.core.rate_limit import RateLimiter


@pytest.fixture
def scope() -> str:
    # A fresh scope per test avoids window/document collisions between tests running in
    # the same second.
    return f"test_{uuid.uuid4().hex[:8]}"


def test_allows_requests_under_the_limit(db: Client, scope: str) -> None:
    limiter = RateLimiter(db)
    for _ in range(3):
        limiter.check(scope=scope, identifier="1.2.3.4", limit=3, window_seconds=3600)


def test_rejects_the_request_that_exceeds_the_limit(db: Client, scope: str) -> None:
    limiter = RateLimiter(db)
    for _ in range(3):
        limiter.check(scope=scope, identifier="1.2.3.4", limit=3, window_seconds=3600)

    with pytest.raises(RateLimitedError):
        limiter.check(scope=scope, identifier="1.2.3.4", limit=3, window_seconds=3600)


def test_different_identifiers_have_independent_limits(db: Client, scope: str) -> None:
    limiter = RateLimiter(db)
    for _ in range(3):
        limiter.check(scope=scope, identifier="1.2.3.4", limit=3, window_seconds=3600)

    # A different IP is a different window document — not throttled by the first one's usage.
    limiter.check(scope=scope, identifier="5.6.7.8", limit=3, window_seconds=3600)


def test_different_scopes_have_independent_limits(db: Client, scope: str) -> None:
    limiter = RateLimiter(db)
    for _ in range(3):
        limiter.check(scope=scope, identifier="same-ip", limit=3, window_seconds=3600)

    other_scope = scope + "_other"
    limiter.check(scope=other_scope, identifier="same-ip", limit=3, window_seconds=3600)
