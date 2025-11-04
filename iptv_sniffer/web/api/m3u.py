"""M3U import/export endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from io import StringIO
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from iptv_sniffer.channel.models import Channel
from iptv_sniffer.m3u.encoding import decode_m3u_bytes
from iptv_sniffer.m3u.generator import M3UGenerator
from iptv_sniffer.m3u.parser import M3UParser
from iptv_sniffer.storage.json_repository import JSONChannelRepository
from iptv_sniffer.web.api.channels import get_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/m3u", tags=["m3u"])


class ImportResult(BaseModel):
    imported: int
    failed: int
    channels: List[Channel]
    errors: List[str] = []


@router.post("/import", response_model=ImportResult)
async def import_m3u(
    file: UploadFile = File(...),
    repository: JSONChannelRepository = Depends(get_repository),
) -> ImportResult:
    if not file.filename or not file.filename.lower().endswith((".m3u", ".m3u8")):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "File must be M3U or M3U8 format"
        )

    content = await file.read()
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")

    decoded = decode_m3u_bytes(content)

    parser = M3UParser()
    playlist = parser.parse(decoded)

    imported_channels: List[Channel] = []
    failed = 0
    errors: List[str] = []

    for item in playlist.channels:
        try:
            channel = Channel(
                name=item.name,
                url=item.url,
                tvg_id=item.tvg_id,
                tvg_logo=item.tvg_logo,
                group=item.group_title,
            )
            saved = await repository.add(channel)
            imported_channels.append(saved)
        except Exception as exc:  # pylint: disable=broad-except
            failed += 1
            logger.warning(
                "Failed importing channel '%s' (%s): %s", item.name, item.url, exc
            )
            errors.append(f"{item.name or item.url}: {exc}")

    logger.info(
        "Imported playlist %s: %s success, %s failed",
        file.filename,
        len(imported_channels),
        failed,
    )

    return ImportResult(
        imported=len(imported_channels),
        failed=failed,
        channels=imported_channels,
        errors=errors[:20],
    )


@router.get("/export")
async def export_m3u(
    group: Optional[str] = Query(None, description="Filter by group title"),
    resolution: Optional[str] = Query(
        None, description="Filter by resolution (e.g. 1080p)"
    ),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        pattern=r"^(online|offline)?$",
        description="Filter by online status",
    ),
    repository: JSONChannelRepository = Depends(get_repository),
) -> StreamingResponse:
    filters: dict[str, str | bool] = {}
    if group:
        filters["group"] = group
    if status_filter == "online":
        filters["is_online"] = True
    elif status_filter == "offline":
        filters["is_online"] = False

    channels = await repository.find_all(filters)
    if resolution:
        channels = [channel for channel in channels if channel.resolution == resolution]

    generator = M3UGenerator()
    output = generator.generate(channels)
    filename = (
        f"iptv_channels_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.m3u"
    )

    logger.info(
        "Exported M3U playlist with %s channels (filters=%s)",
        len(channels),
        {"group": group, "resolution": resolution, "status": status_filter},
    )

    return StreamingResponse(
        StringIO(output),
        media_type="audio/x-mpegurl",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


__all__ = ["router", "get_repository"]
