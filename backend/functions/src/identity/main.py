"""identity — entry point. Every Firebase function this domain deploys, mapped to the
subdomain `main` module that defines it. Nothing is imported here; see the root main.py."""

FUNCTIONS: dict[str, str] = {
    "api_identity_admins": "src.identity.admins.main",
}
