"""ops/audit — entry point: deploys api_ops_audit (admin)."""

from kernel.http import make_function
from src.ops.audit.routes import router

api_ops_audit = make_function(router, name="api_ops_audit")
