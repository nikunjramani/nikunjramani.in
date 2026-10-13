"""identity/admins — entry point: deploys api_identity_admins (admin).

The runtime service account needs roles/firebaseauth.admin to change custom claims
(infra/terraform/modules/iam). The very first admin is still granted with
infra/scripts/set_admin_claim.py — nobody can call this API before one exists."""

from kernel.http import make_function
from src.identity.admins.routes import router

api_identity_admins = make_function(router, name="api_identity_admins")
