from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from iptv_sniffer import __version__
from iptv_sniffer.utils.ffmpeg import check_ffmpeg_installed
from iptv_sniffer.web.api import channels_router, scan_router, screenshots_router

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


static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    logger.info("Serving SPA static files from %s", static_dir)
else:
    logger.warning(
        "Static directory %s not found. Run frontend build to serve SPA.", static_dir
    )

app.include_router(scan_router)
app.include_router(screenshots_router)
app.include_router(channels_router)


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


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_entry(full_path: str, request: Request) -> Response:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")

    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return JSONResponse(
        {
            "message": "Frontend assets not built. Run 'npm run build' from the frontend/ directory.",
            "requested_path": full_path,
        },
        status_code=503,
    )
