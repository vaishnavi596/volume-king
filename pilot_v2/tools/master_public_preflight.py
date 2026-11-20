"""Read-only BOT KING V2 Master public SPKI handoff gate.

This does not enroll a device, prove Android hardware security, deploy a service,
connect to Dhan, or change either V1 or V2 state. Review the fingerprint on
the trusted owner handset before a separate explicit enrollment operation.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
from pathlib import Path

from pilot_v2.device_policy import valid_id
from pilot_v2.tools.provision_oracle_master import _public_spki


def inspect_public_handoff(*, device_id: str, public_path: Path,
                           owner_fingerprint: str) -> dict:
    if not valid_id(device_id):
        raise ValueError("Invalid approved V2 device ID")
    if type(owner_fingerprint) is not str or len(owner_fingerprint) != 64:
        raise ValueError("Owner fingerprint must be 64 hex characters")
    try:
        bytes.fromhex(owner_fingerprint)
    except ValueError:
        raise ValueError("Owner fingerprint must be hexadecimal") from None
    data = _public_spki(Path(public_path))  # canonical P-256 DER; no links/oversize
    actual = hashlib.sha256(data).hexdigest()
    if not hmac.compare_digest(actual, owner_fingerprint.lower()):
        raise ValueError("Phone fingerprint and supplied public key do not match")
    return {"public_spki_verified": True, "fingerprint_sha256": actual,
            "enrolled": False, "android_runtime_verified": False,
            "oracle_activated": False, "orders_enabled": False}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only physical-key handoff inspection (NOT enrollment)")
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--public-spki-der", required=True)
    parser.add_argument("--owner-fingerprint", required=True)
    args = parser.parse_args(argv)
    result = inspect_public_handoff(
        device_id=args.device_id, public_path=Path(args.public_spki_der),
        owner_fingerprint=args.owner_fingerprint)
    print("V2_PUBLIC_HANDOFF_PREFLIGHT=PASS")
    print("V2_PUBLIC_SHA256=" + result["fingerprint_sha256"])
    print("V2_MASTER_ENROLLED=NO")
    print("V2_ANDROID_HARDWARE_PROVEN=NO")
    print("V2_LIVE_ACTIVATED=NO")
    return result


if __name__ == "__main__":
    main()
