"""Firestore collection names that more than one module needs to agree on.

tests/test_domain_registry.py cross-checks CONTENT_COLLECTIONS against the schemas'
publicRead flag, so a new content collection can't be silently left out of backups or
media reference checks.
"""

CONTENT_COLLECTIONS: tuple[str, ...] = (
    "profile",
    "projects",
    "skills",
    "experience",
    "education",
    "certifications",
    "posts",
    "site_config",
)

# Everything worth restoring after a disaster. Rate-limit counters are deliberately absent.
BACKED_UP_COLLECTIONS: tuple[str, ...] = (
    *CONTENT_COLLECTIONS,
    "contact_messages",
    "media_assets",
    "audit_log",
)
