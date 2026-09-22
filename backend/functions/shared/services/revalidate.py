"""Tell the Next.js site that content changed, so ISR-cached pages refresh within seconds.

Best-effort by design: the write has already succeeded by the time this runs, and a failed
cache bust only means a page stays stale until its ISR window expires. Raising here would
turn a successful save into an error the admin then retries for no reason.
"""

from __future__ import annotations

import httpx

from shared.core.config import get_settings
from shared.core.logging import get_logger

log = get_logger(__name__)


def revalidate_tags(*tags: str) -> None:
    settings = get_settings()
    if not settings.revalidate_token:
        # No shared secret configured (fresh local setup): skip rather than send an
        # unauthenticated request the site would reject anyway.
        log.info("REVALIDATE_TOKEN not set - skipping cache revalidation")
        return
    try:
        httpx.post(
            settings.revalidate_url,
            json={"tags": list(tags)},
            headers={"Authorization": f"Bearer {settings.revalidate_token}"},
            timeout=3.0,
        ).raise_for_status()
    except httpx.HTTPError as exc:
        log.warning(
            "revalidation failed",
            extra={"extra_fields": {"tags": list(tags), "error": str(exc)}},
        )
