"""A lightweight spam heuristic. Flags, never blocks — see docs/plan/03-security.md.

This is a personal-site contact form, not a general-purpose abuse pipeline: three cheap
signals (link count, all-caps ratio, repeated characters) catch the overwhelming majority
of what actually shows up in a form like this, and anything more elaborate would be
tuning a model against traffic that does not exist yet.
"""

from __future__ import annotations

import re

_URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
_REPEAT_RE = re.compile(r"(.)\1{6,}")  # the same character 7+ times in a row


def score_spam(message: str) -> float:
    """0.0 (looks fine) to 1.0 (looks like spam). Never raises."""
    if not message:
        return 0.0

    score = 0.0

    link_count = len(_URL_RE.findall(message))
    score += min(link_count * 0.3, 0.6)  # a couple of links is normal; a wall of them isn't

    letters = [c for c in message if c.isalpha()]
    if len(letters) > 20:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.7:
            score += 0.25

    if _REPEAT_RE.search(message):
        score += 0.25

    return min(score, 1.0)
