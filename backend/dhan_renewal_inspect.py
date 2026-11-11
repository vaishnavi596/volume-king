"""Read-only Dhan renewal scheduler inspection; no secrets or network requests.

A real renewal executor must be installed separately after token provenance
and credential storage are verified. This module deliberately cannot renew.
"""
import argparse
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from backend.dhan_renewal_policy import renewal_decision


def inspect(source, expiry, now=None):
    """Produce a non-sensitive decision for operator monitoring."""
    if not isinstance(expiry, str) or not expiry.strip():
        raise ValueError("Expiry timestamp required")
    try:
        parsed = datetime.fromisoformat(expiry.strip().replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Expiry must be ISO-8601") from None
    return renewal_decision(source, parsed, now=now)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect renewal eligibility without modifying tokens")
    parser.add_argument("--source", required=True, choices=["dhan_web", "oauth_consent", "totp_generated", "unknown"])
    parser.add_argument("--expires-at", required=True, help="ISO-8601 timestamp; naive timestamps interpreted as IST")
    args = parser.parse_args(argv)
    result = inspect(args.source, args.expires_at)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
