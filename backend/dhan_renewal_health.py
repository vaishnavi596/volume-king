"""Read-only, secret-free renewal eligibility for the Clone gateway."""
from datetime import datetime, timezone
from backend.dhan_expiry_store import load_expiry_metadata
from backend.dhan_renewal_policy import renewal_decision

def renewal_health_report(metadata_path, *, now=None):
    report={"protocol":"clone-renewal-health-v1","state":"UNVERIFIED",
            "metadata_verified":False,"renewal_observed":False,
            "timer_verified":False,"provider_requests":0,"orders_sent":0}
    if not metadata_path:
        return report
    try:
        metadata=load_expiry_metadata(metadata_path)
        expiry=datetime.fromisoformat(metadata["expires_at"])
        decision=renewal_decision(metadata["source"],expiry,now=now)
    except (OSError,ValueError,TypeError,OverflowError):
        return report
    return dict(report,state=decision["state"].upper(),metadata_verified=True)
