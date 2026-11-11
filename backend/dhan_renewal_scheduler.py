"""Fail-closed expiry scheduler for Dhan Web token rotation.

No renewal occurs unless an operator explicitly supplies a trusted expiry,
verified provenance, and --execute. Timer integrations should invoke this
wrapper, not the raw renewal executor.
"""
import argparse
from datetime import datetime
import os
import json
import urllib.error
from pathlib import Path
import sys

from backend.dhan_renewal_policy import renewal_decision
from backend.dhan_expiry_store import load_expiry_metadata
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
    parser.add_argument("--source", choices=["dhan_web", "oauth_consent", "totp_generated", "unknown"])
    parser.add_argument("--expires-at")
    parser.add_argument("--expiry-file", help="Read owner-private trusted expiry metadata")
    parser.add_argument("--client-id-env", default="DHAN_CLIENT_ID")
    parser.add_argument("--token-file", default="/etc/bot-king/dhan-token")
    parser.add_argument("--lead-minutes", type=int, default=90)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.expiry_file:
            if args.source or args.expires_at:
                raise ValueError("Use expiry file or explicit expiry, not both")
            metadata = load_expiry_metadata(args.expiry_file)
            source, expiry = metadata["source"], metadata["expires_at"]
        else:
            source, expiry = args.source, args.expires_at
        decision = scheduled_decision(source, expiry, lead_minutes=args.lead_minutes)
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
        if not args.expiry_file:
            raise ValueError("Execution requires owner-private expiry file for atomic update")
        client_id = os.environ.get(args.client_id_env, "").strip()
        result = renew_web_token(client_id, Path(args.token_file), expiry_path=Path(args.expiry_file))
        if not isinstance(result, dict) or result.get("profile_verified") is not True:
            print("Renewal failed: profile not verified")
            return 1
        print("Renewal completed and profile verified")
        return 0
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print("Renewal blocked or failed:", type(exc).__name__, "(no secrets logged)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
