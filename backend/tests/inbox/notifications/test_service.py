from __future__ import annotations

import pytest

from src.inbox.notifications.service import render_email


def test_visitor_input_is_html_escaped() -> None:
    _, html = render_email(
        {
            "name": '<a href="https://evil.example">Bank</a>',
            "email": "x@example.com",
            "subject": "<script>alert(1)</script>",
            "message": "<img src=x onerror=alert(1)>\nsecond line",
        }
    )
    assert "<a href" not in html
    assert "<script>" not in html
    assert "<img" not in html
    assert "&lt;script&gt;" in html
    assert "second line" in html
    assert "<br>" in html


def test_spam_note_only_above_threshold() -> None:
    _, flagged = render_email({"name": "A", "message": "m", "spamScore": 0.75})
    _, clean = render_email({"name": "A", "message": "m", "spamScore": 0.1})
    assert "Spam score: 0.75" in flagged
    assert "Spam score" not in clean


def test_newlines_in_name_cannot_split_the_subject() -> None:
    subject, _ = render_email({"name": "A\r\nBcc: someone@example.com", "message": "m"})
    assert "\r" not in subject
    assert "\n" not in subject


def test_notify_owner_skips_without_a_recipient() -> None:
    from unittest.mock import patch

    from src.inbox.notifications import service
    from src.inbox.notifications.settings import NotificationSettings

    with (
        patch.object(
            service,
            "get_notification_settings",
            return_value=NotificationSettings(contact_email_to=""),
        ),
        patch.object(service, "send_email") as send,
    ):
        service.notify_owner("m1", {"name": "A", "message": "m"})
    send.assert_not_called()


def test_notify_owner_sends_the_rendered_email() -> None:
    from unittest.mock import patch

    from src.inbox.notifications import service
    from src.inbox.notifications.settings import NotificationSettings

    with (
        patch.object(
            service,
            "get_notification_settings",
            return_value=NotificationSettings(contact_email_to="me@x.dev"),
        ),
        patch.object(service, "send_email") as send,
    ):
        service.notify_owner("m1", {"name": "A", "message": "hello"})
    assert send.call_args.kwargs["to"] == "me@x.dev"
    assert "hello" in send.call_args.kwargs["html"]
    # The message id: Eventarc redelivering the event must not email twice.
    assert send.call_args.kwargs["idempotency_key"] == "contact-message/m1"


def test_whitespace_placeholder_key_skips_the_send(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import patch

    import httpx

    from src.inbox.notifications import email
    from src.inbox.notifications.settings import NotificationSettings

    monkeypatch.setenv("RESEND_API_KEY", "\n")
    with (
        patch.object(email, "get_notification_settings", return_value=NotificationSettings()),
        patch.object(httpx, "post") as post,
    ):
        email.send_email(to="me@x.dev", subject="s", html="h", idempotency_key="k")
    post.assert_not_called()


@pytest.mark.parametrize(
    ("status", "retried"), [(401, False), (422, False), (409, True), (429, True), (503, True)]
)
def test_only_failures_a_retry_could_fix_raise(
    monkeypatch: pytest.MonkeyPatch, status: int, retried: bool
) -> None:
    """Raising makes the event handler answer 5xx, so Eventarc redelivers for up to a day —
    worth it for an outage or a rate limit, pointless for a bad key or a rejected payload."""
    from unittest.mock import patch

    import httpx

    from src.inbox.notifications import email
    from src.inbox.notifications.settings import NotificationSettings

    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    response = httpx.Response(
        status, request=httpx.Request("POST", "https://api.resend.com/emails")
    )
    with (
        patch.object(email, "get_notification_settings", return_value=NotificationSettings()),
        patch.object(httpx, "post", return_value=response) as post,
    ):
        if retried:
            with pytest.raises(email.EmailDeliveryError):
                email.send_email(to="me@x.dev", subject="s", html="h", idempotency_key="k")
        else:
            email.send_email(to="me@x.dev", subject="s", html="h", idempotency_key="k")
    post.assert_called_once()  # no in-process retries: redelivery is Eventarc's job
    assert post.call_args.kwargs["headers"]["Idempotency-Key"] == "k"


def test_a_network_error_raises_for_redelivery(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import patch

    import httpx

    from src.inbox.notifications import email
    from src.inbox.notifications.settings import NotificationSettings

    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    with (
        patch.object(email, "get_notification_settings", return_value=NotificationSettings()),
        patch.object(httpx, "post", side_effect=httpx.ConnectError("down")),
        pytest.raises(email.EmailDeliveryError),
    ):
        email.send_email(to="me@x.dev", subject="s", html="h", idempotency_key="k")
