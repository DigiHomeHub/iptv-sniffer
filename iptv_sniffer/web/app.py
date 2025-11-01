from __future__ import annotations

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from iptv_sniffer import __version__
from iptv_sniffer.utils.ffmpeg import check_ffmpeg_installed

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting iptv-sniffer v%s", __version__)
    if not check_ffmpeg_installed():
        logger.warning("FFmpeg not detected. Stream validation will be unavailable.")
    yield


app = FastAPI(
    title="iptv-sniffer",
    description="Discover and validate IPTV channels on local networks.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, object]:
    """Return service health information."""
    ffmpeg_available = check_ffmpeg_installed()
    status = "ok" if ffmpeg_available else "degraded"
    return {
        "status": status,
        "version": __version__,
        "checks": {
            "ffmpeg": ffmpeg_available,
        },
    }
