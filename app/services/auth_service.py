from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status

from app.config import settings

logger = logging.getLogger(__name__)


# ─── Password hashing ────────────────────────────────────────────────────────
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


# ─── JWT access tokens ───────────────────────────────────────────────────────
# A JWT is a base64-encoded string with three dot-separated parts:
#   header.payload.signature
# - header   : algorithm metadata (e.g. {"alg":"HS256","typ":"JWT"})
# - payload  : our claims about the user (sub, email, is_admin, exp)
# - signature: HMAC-SHA256(header.payload, JWT_SECRET_KEY)
# The server doesn't need DB lookups to validate — just verifies the signature
# mathematically. That's what makes JWT stateless.

# Fallback signing key used when JWT_SECRET_KEY is empty in the environment.
# Process-local: tokens are invalidated on every restart. Fine for dev only —
# production deployment MUST set JWT_SECRET_KEY in .env.
_FALLBACK_JWT_SECRET = secrets.token_urlsafe(64)


def _jwt_secret() -> str:
    return settings.JWT_SECRET_KEY or _FALLBACK_JWT_SECRET


def create_access_token(*, user_id: str, email: str, is_admin: bool) -> str:
    """
    Build a signed JWT for the given user.

    The payload uses standard JWT claim names where applicable:
      - sub: subject = user id (the canonical identifier)
      - email, is_admin: our custom claims
      - iat: issued-at timestamp
      - exp: expiration timestamp (settings.JWT_EXPIRE_DAYS from now)
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "is_admin": is_admin,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.JWT_EXPIRE_DAYS)).timestamp()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Verify signature + expiry and return the claims dict.
    Raises jwt.InvalidTokenError (or subclass) on any failure.
    """
    return jwt.decode(token, _jwt_secret(), algorithms=[settings.JWT_ALGORITHM])


# ─── FastAPI dependencies ────────────────────────────────────────────────────
# These are plain functions used as `Depends(...)` arguments in route handlers.
# FastAPI runs them automatically before the handler — if they raise an
# HTTPException, the handler never runs and the client sees the error.

class CurrentUser(dict):
    """Thin wrapper around the JWT payload for typing/IDE clarity."""
    @property
    def user_id(self) -> str:
        return str(self["sub"])

    @property
    def email(self) -> str:
        return str(self["email"])

    @property
    def is_admin(self) -> bool:
        return bool(self.get("is_admin", False))


def _extract_bearer_token(request: Request) -> str:
    """Pull token from 'Authorization: Bearer <token>' header."""
    auth_header = request.headers.get("authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


def get_current_user(request: Request) -> CurrentUser:
    """
    Validate the JWT and return the user payload.
    Use as: `user: CurrentUser = Depends(get_current_user)`
    """
    token = _extract_bearer_token(request)
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(payload)


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Like get_current_user, but additionally requires is_admin=True.
    Use to gate dashboard / metrics endpoints.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
