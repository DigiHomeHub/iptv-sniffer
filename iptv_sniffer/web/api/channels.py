"""Channel management API."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from math import ceil
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository
from iptv_sniffer.utils.config import AppConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/channels", tags=["channels"])


def get_repository() -> JSONChannelRepository:
    """Factory for the channel repository (overridable in tests)."""
    config = AppConfig()
    return JSONChannelRepository(config.data_dir / "channels.json")


class ChannelListResponse(BaseModel):
    channels: List[Channel]
    total: int
    page: int
    pages: int


class ChannelUpdateRequest(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_logo: Optional[str] = None
    group: Optional[str] = None


@router.get("", response_model=ChannelListResponse)
async def list_channels(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    group: Optional[str] = Query(None, description="Filter by group title"),
    resolution: Optional[str] = Query(
        None, description="Filter by resolution (e.g. 1080p)"
    ),
    status: Optional[str] = Query(
        None, pattern="^(online|offline)?$", description="Filter by availability"
    ),
    search: Optional[str] = Query(None, description="Search in channel name or URL"),
    repository: JSONChannelRepository = Depends(get_repository),
) -> ChannelListResponse:
    """Return paginated list of channels with optional filters."""
    filters: dict[str, str | bool] = {}
    if group:
        filters["group"] = group
    if status == "online":
        filters["is_online"] = True
    elif status == "offline":
        filters["is_online"] = False

    channels = await repository.find_all(filters)

    if resolution:
        channels = [channel for channel in channels if channel.resolution == resolution]

    if search:
        lowered = search.lower()
        channels = [
            channel
            for channel in channels
            if lowered in (channel.name or "").lower() or lowered in channel.url.lower()
        ]

    total = len(channels)
    pages = max(ceil(total / page_size), 1)
    start = (page - 1) * page_size
    end = start + page_size

    logger.info(
        "Channels listed",
        extra={
            "filters": {
                "group": group,
                "resolution": resolution,
                "status": status,
                "search": search,
            },
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )

    return ChannelListResponse(
        channels=channels[start:end],
        total=total,
        page=page,
        pages=pages,
    )


@router.get("/{channel_id}", response_model=Channel)
async def get_channel(
    channel_id: str, repository: JSONChannelRepository = Depends(get_repository)
) -> Channel:
    """Return channel details by ID."""
    channel = await repository.get_by_id(channel_id)
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )
    return channel


@router.put("/{channel_id}", response_model=Channel)
async def update_channel(
    channel_id: str,
    payload: ChannelUpdateRequest,
    repository: JSONChannelRepository = Depends(get_repository),
) -> Channel:
    """Update channel metadata and mark entry as manually edited."""
    channel = await repository.get_by_id(channel_id)
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )

    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        channel = channel.model_copy(update=update_data)
        channel.manually_edited = True
        channel.updated_at = datetime.now(timezone.utc)
        channel = await repository.add(channel)
        logger.info(
            "Channel updated",
            extra={"channel_id": channel_id, "changes": update_data},
        )

    return channel


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: str, repository: JSONChannelRepository = Depends(get_repository)
) -> dict:
    """Remove channel entry."""
    deleted = await repository.delete(channel_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )

    logger.info("Channel deleted", extra={"channel_id": channel_id})
    return {"deleted": True}


__all__ = ["router", "get_repository"]
