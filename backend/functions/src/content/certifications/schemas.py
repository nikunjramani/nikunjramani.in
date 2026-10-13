"""Wire shapes for content/certifications.

Requests are the Certification model itself, validated by FastAPI against the generated
schema; responses carry the document id beside it."""

from kernel.crud.schemas import RecordOut, ReorderIn
from shared.generated import Certification


class CertificationOut(RecordOut[Certification]):
    """A certifications document as the admin API returns it."""


__all__ = ["CertificationOut", "ReorderIn"]
