"""Master-managed maximum-four-device authorization rules. No secrets or I/O.

The HTTP gateway MUST authenticate the master actor independently using a
server-side revocable session; never trust a claimed role or device ID from a
mobile payload. These are domain rules, NOT a deployed authentication system.
"""
from dataclasses import dataclass, field

MAX_DEVICES = 4
ALLOWED_FEEDS = frozenset(("quotes", "indices", "candles", "scanner",
                           "super_five", "options", "assessment"))

class DevicePolicyError(ValueError):
    pass

def valid_id(value):
    return (type(value) is str and 16 <= len(value) <= 128 and
            all(c.isascii() and (c.isalnum() or c in "-_") for c in value))

@dataclass(frozen=True)
class DeviceGrant:
    device_id: str
    feeds: frozenset
    enabled: bool = True
    master: bool = False

    def __post_init__(self):
        if (not valid_id(self.device_id)
                or type(self.feeds) is not frozenset
                or not self.feeds.issubset(ALLOWED_FEEDS)
                or type(self.enabled) is not bool
                or type(self.master) is not bool):
            raise DevicePolicyError("Invalid device grant")

@dataclass
class DeviceRegistry:
    """Server-side policy state. Caller must enforce verified master auth."""
    grants: dict = field(default_factory=dict)
    master_id: str | None = None

    def enroll_master(self, device_id, *, verified_bootstrap=False):
        if verified_bootstrap is not True or self.master_id is not None or self.grants:
            raise DevicePolicyError("Master enrollment requires authenticated one-time bootstrap")
        grant = DeviceGrant(device_id, ALLOWED_FEEDS, master=True)
        self.grants[device_id] = grant
        self.master_id = device_id

    def assign(self, actor, device_id, feeds, *, enabled=True):
        self._require_master(actor)
        if device_id == self.master_id or not valid_id(device_id):
            raise DevicePolicyError("Cannot overwrite master or invalid device")
        if type(feeds) not in (tuple, list, frozenset, set):
            raise DevicePolicyError("Invalid permitted feeds")
        permission = frozenset(feeds)
        if device_id not in self.grants and len(self.grants) >= MAX_DEVICES:
            raise DevicePolicyError("At most four enrolled devices")
        grant = DeviceGrant(device_id, permission, enabled=enabled)
        self.grants[device_id] = grant

    def revoke(self, actor, device_id):
        self._require_master(actor)
        if device_id == self.master_id:
            raise DevicePolicyError("Master cannot be revoked by delegated action")
        self.grants.pop(device_id, None)

    def can_access(self, device_id, feed):
        grant = self.grants.get(device_id)
        return bool(grant and grant.enabled and feed in grant.feeds)

    def _require_master(self, actor):
        grant = self.grants.get(actor)
        if actor != self.master_id or not grant or not grant.master or not grant.enabled:
            raise DevicePolicyError("Verified master session required")
