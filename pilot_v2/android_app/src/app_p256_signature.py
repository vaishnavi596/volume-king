"""Canonical P-256 ECDSA DER signature validation at Android Keystore boundary.

Format validation only: NOT a signature verification, proof of key storage,
device attestation, or authorization. The server must verify the signature
against the independently enrolled public key.
"""

P256_ORDER = int(
    "FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16)


def is_canonical_p256_der_signature(value):
    """Reject non-DER, zero/out-of-range r/s and padded integers."""
    if (type(value) is not bytes or not 8 <= len(value) <= 72
            or value[0] != 0x30 or value[1] != len(value) - 2):
        return False
    offset = 2
    components = []
    for _ in range(2):
        if offset + 2 > len(value) or value[offset] != 0x02:
            return False
        size = value[offset + 1]
        offset += 2
        if size < 1 or size > 33 or offset + size > len(value):
            return False
        integer = value[offset:offset + size]
        offset += size
        if integer[0] & 0x80:
            return False  # Signed DER negative INTEGER.
        if size > 1 and integer[0] == 0 and not (integer[1] & 0x80):
            return False  # Non-minimal DER positive INTEGER.
        number = int.from_bytes(integer, "big")
        if not 1 <= number < P256_ORDER:
            return False
        components.append(number)
    return offset == len(value) and len(components) == 2
