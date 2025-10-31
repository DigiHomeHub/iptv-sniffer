from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class M3UChannel(BaseModel):
    """
    Parsed representation of a channel entry from an M3U playlist.

    Only a subset of commonly supported attributes are captured here to keep the
    model broadly compatible across IPTV playlists.
    """

    name: str = Field(..., min_length=1, description="Human readable channel name.")
    url: str = Field(
        ..., min_length=1, description="Stream URL associated with the channel."
    )
    tvg_id: Optional[str] = Field(
        default=None,
        description="Channel identifier used by XMLTV or EPG providers.",
    )
    tvg_name: Optional[str] = Field(
        default=None,
        description="Alternative channel display name supplied by the playlist.",
    )
    tvg_logo: Optional[str] = Field(
        default=None,
        description="Logo URL for the channel if provided in the playlist.",
    )
    group_title: Optional[str] = Field(
        default=None,
        description="Grouping value extracted from group-title or #EXTGRP metadata.",
    )

    model_config = ConfigDict(frozen=True, extra="ignore")


class M3UPlaylist(BaseModel):
    """Container of parsed playlist channels."""

    channels: List[M3UChannel] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True, extra="forbid")
