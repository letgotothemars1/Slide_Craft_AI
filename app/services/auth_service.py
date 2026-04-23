from __future__ import annotations

import hashlib
import hmac
import secrets


# PBKDF2 settings are explicit, so hashes remain reproducible and verifiable.
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 390_000
PBKDF2_SALT_BYTES = 16


def _pbkdf2(password: str, *, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        iterations,
    )


def hash_password(password: str) -> str:
    """
    Create password hash for DB storage.
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<digest_hex>
    """
    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    digest = _pbkdf2(password, salt=salt, iterations=PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time password verification."""
    try:
        scheme, iterations_raw, salt_hex, digest_hex = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False

        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
    except Exception:
        return False

    actual_digest = _pbkdf2(password, salt=salt, iterations=iterations)
    return hmac.compare_digest(actual_digest, expected_digest)
