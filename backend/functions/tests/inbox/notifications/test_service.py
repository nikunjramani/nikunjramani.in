from __future__ import annotations

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
        service.notify_owner({"name": "A", "message": "m"})
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
        service.notify_owner({"name": "A", "message": "hello"})
    assert send.call_args.kwargs["to"] == "me@x.dev"
    assert "hello" in send.call_args.kwargs["html"]
