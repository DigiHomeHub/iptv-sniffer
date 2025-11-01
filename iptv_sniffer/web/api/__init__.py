"""API routers for the iptv-sniffer web service."""

from .scan import router as scan_router

__all__ = ["scan_router"]
