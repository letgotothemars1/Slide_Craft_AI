from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from pathlib import Path
import re
import shutil
from urllib import error, parse, request

from app.config import settings

SAFE_KEY_PATTERN = re.compile(r"[^A-Za-z0-9._/-]")
logger = logging.getLogger(__name__)


class StorageService(ABC):
    """Common interface for storage operations used by generator."""

    @abstractmethod
    def upload_file(self, local_path: Path, storage_key: str, content_type: str) -> str:
        """Upload local file and return downloadable URL."""

    @abstractmethod
    def upload_bytes(self, bytes_data: bytes, storage_key: str, content_type: str) -> str:
        """Upload bytes payload and return downloadable URL."""

    @abstractmethod
    def get_public_url(self, storage_key: str) -> str:
        """Build downloadable URL for existing object key."""


def _normalize_key(storage_key: str) -> str:
    """Normalize object key and prevent path traversal."""
    key = storage_key.strip().lstrip("/")
    normalized = Path(key).as_posix()
    parts = [part for part in normalized.split("/") if part not in {"", ".", ".."}]
    ascii_key = "/".join(parts)
    # Keep storage keys strictly ASCII to avoid latin-1/HTTP header edge-cases.
    return SAFE_KEY_PATTERN.sub("_", ascii_key)


def _quote_key(storage_key: str) -> str:
    """URL-encode storage key while preserving path separators."""
    return parse.quote(_normalize_key(storage_key), safe="/-_.~")


def _ensure_ascii_http_value(name: str, value: str) -> None:
    """Fail fast if non-ASCII appears in HTTP-sensitive values."""
    try:
        name.encode("ascii")
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise RuntimeError(f"Non-ASCII HTTP value detected: {name}={value!r}") from exc


class LocalStorageService(StorageService):
    """Local fallback storage for development."""

    def __init__(self) -> None:
        self.root = settings.STORAGE_PATH

    def upload_file(self, local_path: Path, storage_key: str, content_type: str) -> str:
        key = _normalize_key(storage_key)
        destination = self.root / key
        logger.debug("Local upload_file: source=%s destination=%s", local_path, destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, destination)
        return self.get_public_url(key)

    def upload_bytes(self, bytes_data: bytes, storage_key: str, content_type: str) -> str:
        key = _normalize_key(storage_key)
        destination = self.root / key
        logger.debug("Local upload_bytes: destination=%s size=%s", destination, len(bytes_data))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(bytes_data)
        return self.get_public_url(key)

    def get_public_url(self, storage_key: str) -> str:
        key = _normalize_key(storage_key)
        return f"{settings.BASE_URL.rstrip('/')}/files/{key}"


class SupabaseStorageService(StorageService):
    """Supabase Storage implementation via REST API and service role key."""

    def __init__(self) -> None:
        if not settings.supabase_storage_enabled:
            raise RuntimeError("Supabase Storage is not configured")

        self.base_url = (settings.SUPABASE_URL or "").rstrip("/")
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY or ""
        self.bucket = settings.SUPABASE_STORAGE_BUCKET or ""

    def upload_file(self, local_path: Path, storage_key: str, content_type: str) -> str:
        data = local_path.read_bytes()
        return self.upload_bytes(data, storage_key, content_type)

    def upload_bytes(self, bytes_data: bytes, storage_key: str, content_type: str) -> str:
        key = _normalize_key(storage_key)
        encoded_key = _quote_key(key)
        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{encoded_key}"
        _ensure_ascii_http_value("url", url)
        _ensure_ascii_http_value("content_type", content_type)

        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": content_type,
            # Upsert is important for retries with the same key.
            "x-upsert": "true",
        }
        for header_name, header_value in headers.items():
            _ensure_ascii_http_value(header_name, header_value)

        logger.debug(
            "Supabase upload: bucket=%s key=%s url=%s content_type=%s bytes=%s",
            self.bucket,
            key,
            url,
            content_type,
            len(bytes_data),
        )

        req = request.Request(url=url, data=bytes_data, headers=headers, method="POST")

        try:
            with request.urlopen(req) as response:
                response.read()
        except error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            logger.exception(
                "Supabase upload HTTPError: bucket=%s key=%s status=%s",
                self.bucket,
                key,
                exc.code,
            )
            raise RuntimeError(
                f"Supabase upload failed ({exc.code}) for key '{key}': {payload}"
            ) from exc

        return self.get_public_url(key)

    def get_public_url(self, storage_key: str) -> str:
        # Requires bucket (or object) to be publicly accessible.
        encoded_key = _quote_key(storage_key)
        return f"{self.base_url}/storage/v1/object/public/{self.bucket}/{encoded_key}"


def get_storage_service() -> StorageService:
    """Factory: Supabase when configured, otherwise local storage fallback."""
    if settings.supabase_storage_enabled:
        return SupabaseStorageService()
    return LocalStorageService()
