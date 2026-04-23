from __future__ import annotations

import base64
import logging
from urllib import request

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIImageService:
    """Thin wrapper over OpenAI Images API for slide visuals."""

    def __init__(self) -> None:
        if not settings.openai_image_enabled:
            raise RuntimeError("OpenAI image generation is not configured")

        # Lazy import: startup remains lightweight until image generation is used.
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_IMAGE_MODEL or ""
        self.size = settings.OPENAI_IMAGE_SIZE
        self.quality = settings.OPENAI_IMAGE_QUALITY
        self.background = settings.OPENAI_IMAGE_BACKGROUND

    def generate_slide_image(
        self,
        prompt: str,
        *,
        job_id: str | None = None,
        slide_id: str | None = None,
    ) -> bytes | None:
        """Generate one image for a slide. Returns bytes or None on any failure."""
        if not prompt.strip():
            return None

        try:
            logger.debug(
                "image.request.started job_id=%s slide_id=%s model=%s size=%s quality=%s background=%s",
                job_id,
                slide_id,
                self.model,
                self.size,
                self.quality,
                self.background,
            )

            payload: dict[str, object] = {
                "model": self.model,
                "prompt": prompt,
            }
            if self.size:
                payload["size"] = self.size
            if self.quality:
                payload["quality"] = self.quality
            if self.background:
                payload["background"] = self.background

            response = self.client.images.generate(**payload)
            data = getattr(response, "data", None) or []
            if not data:
                logger.warning("image.error reason=no_data")
                return None

            item = data[0]
            b64_json = getattr(item, "b64_json", None)
            if isinstance(b64_json, str) and b64_json:
                image_bytes = base64.b64decode(b64_json)
                logger.debug(
                    "image.response.received job_id=%s slide_id=%s source=b64 bytes=%s",
                    job_id,
                    slide_id,
                    len(image_bytes),
                )
                return image_bytes

            image_url = getattr(item, "url", None)
            if isinstance(image_url, str) and image_url:
                with request.urlopen(image_url, timeout=20) as resp:
                    image_bytes = resp.read()
                logger.debug(
                    "image.response.received job_id=%s slide_id=%s source=url bytes=%s",
                    job_id,
                    slide_id,
                    len(image_bytes),
                )
                return image_bytes

            logger.warning(
                "image.error job_id=%s slide_id=%s reason=no_b64_or_url",
                job_id,
                slide_id,
            )
            return None
        except Exception:
            logger.exception("image.error job_id=%s slide_id=%s", job_id, slide_id)
            return None


def get_image_service() -> OpenAIImageService:
    return OpenAIImageService()
