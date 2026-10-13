"""ops — entry point. Every Firebase function this domain deploys, by name, mapped to the
subdomain `main` module that defines it. Nothing is imported here: the root main.py loads
only the module FUNCTION_TARGET names, so one function's cold start never builds another."""

FUNCTIONS: dict[str, str] = {
    "api_ops_health": "src.ops.health.main",
    "api_ops_audit": "src.ops.audit.main",
    "nightly_backup": "src.ops.backup.main",
}
