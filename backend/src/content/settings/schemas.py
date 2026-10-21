"""Wire shapes for content/settings.

Requests are the SiteConfig model itself, validated by FastAPI against the generated
schema; responses carry the document id beside it."""

from kernel.crud.schemas import RecordOut
from shared.generated import SiteConfig


class SiteConfigOut(RecordOut[SiteConfig]):
    """A site_config document as the admin API returns it."""
