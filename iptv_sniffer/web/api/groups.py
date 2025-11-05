"""Group management API for channel organization."""

from __future__ import annotations

import logging
from collections import defaultdict
from math import ceil
from typing import Dict, Iterable, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository
from iptv_sniffer.web.api.channels import get_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/groups", tags=["groups"])


class GroupStatistics(BaseModel):
    """Aggregate information about a channel group."""

    name: str
    total: int
    online: int
    offline: int
    online_percentage: float = Field(ge=0, le=100)


class GroupListResponse(BaseModel):
    """Response payload for group listing."""

    groups: List[GroupStatistics]
    total_groups: int


class GroupChannelsResponse(BaseModel):
    """Paginated list of channels contained within a group."""

    channels: List[Channel]
    total: int
    page: int
    pages: int


class MergeGroupsRequest(BaseModel):
    """Merge multiple source groups into a target group."""

    source_groups: List[str] = Field(min_length=1)
    target_group: str = Field(min_length=1)


class RenameGroupRequest(BaseModel):
    """Rename an existing group."""

    new_name: str = Field(min_length=1)


def _canonical_group(name: str) -> Optional[str]:
    """Convert API group identifiers to storage representation."""
    return None if name.lower() == "uncategorized" else name


def _display_name(group: Optional[str]) -> str:
    """Provide user-facing label for a group."""
    return group if group is not None else "Uncategorized"


@router.get("", response_model=GroupListResponse)
async def list_groups(
    repository: JSONChannelRepository = Depends(get_repository),
) -> GroupListResponse:
    """Return all groups with summary statistics."""
    all_channels = await repository.find_all()
    grouped: Dict[Optional[str], List[Channel]] = defaultdict(list)

    for channel in all_channels:
        grouped[channel.group].append(channel)

    stats: List[GroupStatistics] = []
    for raw_group, members in grouped.items():
        if not members:
            continue
        online = sum(1 for ch in members if ch.is_online)
        offline = len(members) - online
        percentage = round((online / len(members)) * 100, 1) if members else 0.0
        stats.append(
            GroupStatistics(
                name=_display_name(raw_group),
                total=len(members),
                online=online,
                offline=offline,
                online_percentage=percentage,
            )
        )

    stats.sort(key=lambda item: item.total, reverse=True)
    logger.info("Listed %s groups", len(stats))
    return GroupListResponse(groups=stats, total_groups=len(stats))


@router.get("/{group_name}/channels", response_model=GroupChannelsResponse)
async def get_group_channels(
    group_name: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    repository: JSONChannelRepository = Depends(get_repository),
) -> GroupChannelsResponse:
    """Return paginated list of channels in a given group."""
    target_group = _canonical_group(group_name)
    channels = await repository.find_all()

    filtered = [channel for channel in channels if channel.group == target_group]

    total = len(filtered)
    pages = max(ceil(total / page_size), 1)
    start = (page - 1) * page_size
    end = start + page_size

    logger.info(
        "Retrieved channels for group",
        extra={
            "group": group_name,
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )

    return GroupChannelsResponse(
        channels=filtered[start:end],
        total=total,
        page=page,
        pages=pages,
    )


async def _update_channels_group(
    repository: JSONChannelRepository,
    channels: Iterable[Channel],
    new_group: Optional[str],
) -> int:
    """Internal helper to persist group updates."""
    updated_count = 0
    for channel in channels:
        updated = channel.model_copy(update={"group": new_group})
        await repository.add(updated)
        updated_count += 1
    return updated_count


@router.post("/merge")
async def merge_groups(
    request: MergeGroupsRequest,
    repository: JSONChannelRepository = Depends(get_repository),
) -> dict:
    """Merge multiple groups into a single target group."""
    target = _canonical_group(request.target_group)
    source_groups = {_canonical_group(name) for name in request.source_groups}

    if target in source_groups:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Target group must be different from source groups.",
        )

    all_channels = await repository.find_all()
    channels_to_merge = [
        channel for channel in all_channels if channel.group in source_groups
    ]

    if not channels_to_merge:
        logger.info(
            "Merge requested but no channels matched sources",
            extra={"sources": request.source_groups},
        )
        return {"merged": 0, "target_group": request.target_group}

    merged_count = await _update_channels_group(repository, channels_to_merge, target)
    logger.info(
        "Merged %s channels into %s",
        merged_count,
        request.target_group,
    )
    return {"merged": merged_count, "target_group": request.target_group}


@router.put("/{group_name}")
async def rename_group(
    group_name: str,
    request: RenameGroupRequest,
    repository: JSONChannelRepository = Depends(get_repository),
) -> dict:
    """Rename a group by updating all associated channels."""
    current_group = _canonical_group(group_name)
    if current_group is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "The 'Uncategorized' group cannot be renamed.",
        )

    new_group = _canonical_group(request.new_name)
    if new_group is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "New group name cannot be 'Uncategorized'.",
        )

    all_channels = await repository.find_all()
    affected = [channel for channel in all_channels if channel.group == current_group]

    if not affected:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Group '{group_name}' not found.",
        )

    renamed = await _update_channels_group(repository, affected, new_group)
    logger.info("Renamed group %s -> %s", group_name, request.new_name)
    return {"renamed": renamed, "new_name": request.new_name}


@router.delete("/{group_name}")
async def delete_group(
    group_name: str,
    repository: JSONChannelRepository = Depends(get_repository),
) -> dict:
    """Delete a group by moving members to the uncategorized pool."""
    current_group = _canonical_group(group_name)
    if current_group is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "The 'Uncategorized' group cannot be deleted.",
        )

    all_channels = await repository.find_all()
    affected = [channel for channel in all_channels if channel.group == current_group]

    if not affected:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Group '{group_name}' not found.",
        )

    updated = await _update_channels_group(repository, affected, None)
    logger.info(
        "Deleted group %s (%s channels moved to Uncategorized)", group_name, updated
    )
    return {"deleted": True, "affected_channels": updated}


__all__ = ["router"]
