"""Settings the whole service needs, and the base every settings class builds on.

Domain-specific settings (buckets, API keys, addresses) live in that domain's own settings
module, so the kernel knows no domain. Each subclasses `ServiceSettings`.

Defaults exist for local development and name the production project and its buckets. A
deployed service must never fall back to them — a line missing from staging's
deploy/<project>.yaml would point staging at production — so in production every field in
`required_in_production` has to come from the environment, and apps/api.py builds every
settings class at startup: a missing value stops the revision before it takes traffic.
"""

from functools import lru_cache
from typing import ClassVar, Literal, Self

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    # Whitespace counts as empty: Secret Manager rejects an empty version, so a secret not
    # set up yet is bound as a single newline (.docs/RUNBOOK.md, Contact form keys).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", str_strip_whitespace=True)

    #: Fields a production deploy must set explicitly (see the module docstring).
    required_in_production: ClassVar[tuple[str, ...]] = ()

    def _in_production(self) -> bool:
        return get_settings().is_production

    @model_validator(mode="after")
    def _set_explicitly_in_production(self) -> Self:
        if self.required_in_production and self._in_production():
            missing = [f for f in self.required_in_production if f not in self.model_fields_set]
            if missing:
                raise ValueError(f"not set in production: {', '.join(missing)}")
        return self


class Settings(ServiceSettings):
    required_in_production = ("firebase_project_id", "service_url")

    # Cloud Run gets GOOGLE_CLOUD_PROJECT from backend/deploy/<project>.yaml; FIREBASE_PROJECT_ID
    # wins locally (.env).
    firebase_project_id: str = Field(
        default="nikunjramani-in",
        validation_alias=AliasChoices("FIREBASE_PROJECT_ID", "GOOGLE_CLOUD_PROJECT"),
    )
    environment: Literal["development", "production"] = "development"
    allowed_origins: str = "http://localhost:3000"
    # This service's own URLs, comma-separated (Cloud Run serves one service at more than one):
    # the audiences Eventarc and Cloud Scheduler may sign their tokens for (kernel/events.py).
    # Empty locally, where /internal/* accepts unsigned calls.
    service_url: str = ""

    def _in_production(self) -> bool:
        return self.is_production

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def service_audiences(self) -> list[str]:
        return [u.strip() for u in self.service_url.split(",") if u.strip()]

    @property
    def runtime_service_account(self) -> str:
        """Created by infra/terraform/modules/iam. The service runs as it, and Eventarc and
        Cloud Scheduler sign their calls to /internal/* as it — the name predates Cloud Run."""
        return f"functions-runtime@{self.firebase_project_id}.iam.gserviceaccount.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
