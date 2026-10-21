"""The shape every repository returns: a validated model plus the document id it lives at.

The generated schemas never carry an `id` field — every one sets additionalProperties to
false, so injecting one would fail validation. The id travels alongside the model instead.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Record[T]:
    id: str
    data: T
