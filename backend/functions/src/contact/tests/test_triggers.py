from __future__ import annotations

from src.contact.triggers import render_email


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
