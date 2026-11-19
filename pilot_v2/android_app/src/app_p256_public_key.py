"""Pure Android-boundary P-256 public-key format gate (stdlib only).

Only a PUBLIC SubjectPublicKeyInfo DER byte string may be returned here.
A real native Android Keystore plugin must independently enforce a
non-exportable private key and provide the public bytes. Format is NOT
hardware attestation or proof of trusted enrollment.
"""
# Strict RFC 5480/SEC1: id-ecPublicKey + prime256v1 + uncompressed point.
P256_SPKI_PREFIX = bytes.fromhex(
    "3059301306072a8648ce3d020106082a8648ce3d03010703420004")
P256_PRIME = int(
    "FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF", 16)
P256_B = int(
    "5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B", 16)


def canonical_p256_public_spki(value):
    """Return True only for an on-curve uncompressed P-256 public SPKI."""
    if (type(value) is not bytes or
            len(value) != len(P256_SPKI_PREFIX) + 64 or
            not value.startswith(P256_SPKI_PREFIX)):
        return False
    point = value[len(P256_SPKI_PREFIX):]
    x = int.from_bytes(point[:32], "big")
    y = int.from_bytes(point[32:], "big")
    if x >= P256_PRIME or y >= P256_PRIME:
        return False
    return (y * y - (x * x * x - 3 * x + P256_B)) % P256_PRIME == 0


def export_validated_p256_public_spki(platform_export):
    """Use an external native public-key exporter; never request private bytes.

    The caller must separately establish that the callback is a trusted
    Android Keystore implementation and that the server-approved device
    identity owns the key; no boolean flag here can assert that provenance.
    """
    if not callable(platform_export):
        raise ValueError("Android public-key exporter unavailable")
    try:
        public = platform_export()
    except Exception:
        raise ValueError("Approved P-256 public key unavailable") from None
    if not canonical_p256_public_spki(public):
        raise ValueError("Invalid canonical P-256 public key")
    return public
