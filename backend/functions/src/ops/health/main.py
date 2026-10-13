"""ops/health — entry point: deploys api_ops_health (public, no auth)."""

from kernel.http import make_function
from src.ops.health.routes import router

api_ops_health = make_function(router, name="api_ops_health")
