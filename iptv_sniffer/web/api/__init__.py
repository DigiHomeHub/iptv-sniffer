"""API routers for the iptv-sniffer web service."""

from .channels import router as channels_router
from .groups import router as groups_router
from .m3u import router as m3u_router
from .scan import router as scan_router
from .screenshots import router as screenshots_router

__all__ = [
    "channels_router",
    "groups_router",
    "m3u_router",
    "scan_router",
    "screenshots_router",
]
