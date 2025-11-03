"""Screenshot serving endpoints."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from iptv_sniffer.utils.config import AppConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/screenshots", tags=["screenshots"])


def _resolve_screenshot_path(filename: str, config: AppConfig) -> Path:
    screenshot_dir = config.screenshot_dir
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    if ".." in filename or filename.startswith("/"):
        logger.error("Blocked suspicious screenshot path: %s", filename)
        raise HTTPException(status_code=403, detail="Access denied")

    relative_path = Path(filename)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        logger.error("Blocked suspicious screenshot path: %s", filename)
        raise HTTPException(status_code=403, detail="Access denied")

    candidate = (screenshot_dir / relative_path).resolve(strict=False)
    root = screenshot_dir.resolve()

    if root not in candidate.parents:
        logger.error("Blocked screenshot access outside directory: %s", filename)
        raise HTTPException(status_code=403, detail="Access denied")

    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")

    return candidate


@router.get("/{filename}")
async def get_screenshot(filename: str) -> FileResponse:
    """Return a cached screenshot image."""
    config = AppConfig()
    path = _resolve_screenshot_path(filename, config)

    return FileResponse(
        path,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=3600, immutable",
            "X-Content-Type-Options": "nosniff",
        },
    )
