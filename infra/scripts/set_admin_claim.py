#!/usr/bin/env python3
"""Grant (or revoke) the admin custom claim.

Signing in with Google is not authorisation — anyone can do that. The `admin: true`
custom claim is the actual gate, and it can only be set server-side. See ADR 0007.

Usage:
    python infra/scripts/set_admin_claim.py <email>
    python infra/scripts/set_admin_claim.py <email> --revoke

Requires application-default credentials for the project:
    gcloud auth application-default login --account=you@example.com
"""

from __future__ import annotations

import argparse
import sys

import firebase_admin
from firebase_admin import auth


def main() -> int:
    parser = argparse.ArgumentParser(description="Set or revoke the admin claim.")
    parser.add_argument("email", help="Email of the Firebase Auth user")
    parser.add_argument("--project", default="nikunjramani-in")
    parser.add_argument("--revoke", action="store_true", help="Remove the claim instead")
    args = parser.parse_args()

    firebase_admin.initialize_app(options={"projectId": args.project})

    try:
        user = auth.get_user_by_email(args.email)
    except auth.UserNotFoundError:
        print(f"✗ No user with email {args.email}.")
        print("  Sign in to the site once first — the user is created on first sign-in.")
        return 1

    claims = dict(user.custom_claims or {})
    if args.revoke:
        claims.pop("admin", None)
    else:
        claims["admin"] = True

    auth.set_custom_user_claims(user.uid, claims)

    verb = "revoked from" if args.revoke else "granted to"
    print(f"✓ admin claim {verb} {args.email} (uid {user.uid})")
    print("  The claim lands in the NEXT token issued — sign out and back in to pick it up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
