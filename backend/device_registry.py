"""B256 device registry: per-phone keys under one master key. Pure logic + one JSON file, no network.

Master key (the existing SSK) is never stored here. Enrolment: the master asks for a one-time code
(10 minutes, single use); a clone app redeems it for its OWN device key. Only SHA-256 hashes of codes and
keys are stored. A disabled device is refused with DEVICE_DISABLED; the owner can enable it again later.
"""
import hashlib
import json
import os
import secrets
import tempfile
import threading
import time

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # no 0/O/1/I
CODE_LENGTH = 8
CODE_TTL_SECONDS = 600
MAX_PENDING_CODES = 5
MAX_DEVICES = 8
MAX_FAILED_REDEEMS = 10
FAIL_WINDOW_SECONDS = 600
KEY_PREFIX = "bkd_"
SAVE_EVERY_SECONDS = 60


class DeviceDisabled(Exception):
    pass


class RedeemLocked(Exception):
    pass


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def clean_name(name):
    text = " ".join(str(name or "").split())[:24]
    return "".join(ch for ch in text if ch.isprintable()) or "Clone"


class DeviceRegistry:
    def __init__(self, path, clock=time.time):
        self.path = path
        self.clock = clock
        self.lock = threading.Lock()
        self.devices = {}
        self.codes = {}          # code hash -> {"name", "expires"}
        self.failures = []       # timestamps of bad redeem attempts
        self._dirty_at = 0.0
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                self.devices = {k: v for k, v in (data.get("devices") or {}).items()
                                if isinstance(v, dict) and isinstance(v.get("key_hash"), str)}
        except (OSError, ValueError):
            self.devices = {}

    def _save(self):
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".devices-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"devices": self.devices}, fh)
            os.chmod(tmp, 0o600)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self._dirty_at = 0.0

    def create_code(self, name):
        with self.lock:
            now = self.clock()
            self.codes = {h: v for h, v in self.codes.items() if v["expires"] > now}
            if len(self.codes) >= MAX_PENDING_CODES:
                raise ValueError("too many pending codes")
            if len(self.devices) >= MAX_DEVICES:
                raise ValueError("device limit reached")
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
            self.codes[_hash(code)] = {"name": clean_name(name), "expires": now + CODE_TTL_SECONDS}
            return {"code": code, "name": clean_name(name), "expires_in": CODE_TTL_SECONDS}

    def redeem(self, code):
        with self.lock:
            now = self.clock()
            self.failures = [t for t in self.failures if now - t < FAIL_WINDOW_SECONDS]
            if len(self.failures) >= MAX_FAILED_REDEEMS:
                raise RedeemLocked()
            entry = None
            if isinstance(code, str) and 4 <= len(code) <= 16:
                entry = self.codes.pop(_hash(code.strip().upper()), None)
            if entry is None or entry["expires"] <= now:
                self.failures.append(now)
                return None
            if len(self.devices) >= MAX_DEVICES:
                return None
            device_id = secrets.token_hex(4)
            key = KEY_PREFIX + secrets.token_urlsafe(30)
            self.devices[device_id] = {"name": entry["name"], "key_hash": _hash(key), "enabled": True,
                                       "created": int(now), "last_seen": None}
            self._save()
            return {"device_id": device_id, "device_key": key, "name": entry["name"]}

    def check(self, key):
        """Return the device record for a valid enabled key; raise DeviceDisabled for a disabled one."""
        if not isinstance(key, str) or not key.startswith(KEY_PREFIX) or len(key) > 128:
            return None
        digest = _hash(key)
        with self.lock:
            for device_id, dev in self.devices.items():
                if secrets.compare_digest(dev["key_hash"], digest):
                    if not dev.get("enabled", True):
                        raise DeviceDisabled()
                    now = self.clock()
                    dev["last_seen"] = int(now)
                    if now - self._dirty_at >= SAVE_EVERY_SECONDS:
                        self._save()
                        self._dirty_at = now
                    return dict(dev, id=device_id)
        return None

    def listing(self):
        with self.lock:
            return [{"id": i, "name": d["name"], "enabled": bool(d.get("enabled", True)),
                     "created": d.get("created"), "last_seen": d.get("last_seen")}
                    for i, d in sorted(self.devices.items(), key=lambda kv: kv[1].get("created") or 0)]

    def set_enabled(self, device_id, enabled):
        with self.lock:
            if device_id not in self.devices:
                raise KeyError(device_id)
            self.devices[device_id]["enabled"] = bool(enabled)
            self._save()

    def delete(self, device_id):
        with self.lock:
            if device_id not in self.devices:
                raise KeyError(device_id)
            del self.devices[device_id]
            self._save()
