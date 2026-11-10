"""Fail-closed expiry scheduler for Dhan Web token rotation.

No renewal occurs unless an operator explicitly supplies a trusted expiry,
verified provenance, and --execute. Timer integrations should invoke this
wrapper, not the raw renewal executor.
"""
import argparse
from datetime import datetime
import os
from pathlib import Path
import sys

from backend.dhan_renewal_policy import renewal_decision
from backend.dhan_web_token_renew import renew_web_token


def scheduled_decision(source, expiry, now=None, lead_minutes=90):
    if not isinstance(expiry, str) or not expiry.strip():
        raise ValueError("Trusted expiry is required")
    try:
        timestamp = datetime.fromisoformat(expiry.strip().replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Invalid expiry timestamp") from None
    return renewal_decision(source, timestamp, now=now, lead_minutes=lead_minutes)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Guarded Dhan Web renewal")
    parser.add_argument("--source", required=True, choices=["dhan_web", "oauth_consent", "totp_generated", "unknown"])
    parser.add_argument("--expires-at", required=True)
    parser.add_argument("--client-id-env", default="DHAN_CLIENT_ID")
    parser.add_argument("--token-file", default="/etc/bot-king/dhan-token")
    parser.add_argument("--lead-minutes", type=int, default=90)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        decision = scheduled_decision(args.source, args.expires_at, lead_minutes=args.lead_minutes)
        state = decision["state"]
        if state == "valid":
            print("Renewal not due")
            return 0
        if state != "renewal_due":
            print("Renewal blocked:", state)
            return 2
        if not args.execute:
            print("Renewal due; dry run only")
            return 0
        client_id = os.environ.get(args.client_id_env, "").strip()
        result = renew_web_token(client_id, Path(args.token_file))
        print("Renewal completed and profile verified" if result["profile_verified"] else "Renewal failed")
        return 0
    except (OSError, ValueError) as exc:
        print("Renewal blocked or failed:", type(exc).__name__, "(no secrets logged)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
