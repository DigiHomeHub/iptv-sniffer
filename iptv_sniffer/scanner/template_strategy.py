"""Template-based scan strategy for generating HTTP probe targets."""

from __future__ import annotations

import ipaddress
from typing import AsyncIterator, Iterable

from .strategy import ScanStrategy

__all__ = ["TemplateScanStrategy"]


class TemplateScanStrategy(ScanStrategy):
    """Generate stream URLs from an IP range and base URL template."""

    _PLACEHOLDER = "{ip}"
    _MAX_RANGE = 1024

    def __init__(self, base_url: str, start_ip: str, end_ip: str) -> None:
        if self._PLACEHOLDER not in base_url:
            raise ValueError(f"base_url must contain placeholder {self._PLACEHOLDER}")

        self.base_url = base_url
        self._start_ip = ipaddress.IPv4Address(start_ip)
        self._end_ip = ipaddress.IPv4Address(end_ip)

        if self._start_ip > self._end_ip:
            raise ValueError("start_ip must be less than or equal to end_ip")

        self._ip_addresses = self._generate_ip_range(self._start_ip, self._end_ip)
        self._validate_private_range(self._ip_addresses)
        self._count = len(self._ip_addresses)
        if self._count > self._MAX_RANGE:
            raise ValueError(
                f"IP range exceeds maximum allowed size of {self._MAX_RANGE}"
            )

    @staticmethod
    def _generate_ip_range(
        start: ipaddress.IPv4Address, end: ipaddress.IPv4Address
    ) -> list[ipaddress.IPv4Address]:
        count = int(end) - int(start) + 1
        return [ipaddress.IPv4Address(int(start) + offset) for offset in range(count)]

    @staticmethod
    def _validate_private_range(ips: Iterable[ipaddress.IPv4Address]) -> None:
        if not all(ip.is_private for ip in ips):
            raise ValueError("Only RFC1918 private IP ranges are supported.")

    def estimate_target_count(self) -> int:
        return self._count

    async def generate_targets(self) -> AsyncIterator[str]:
        for ip in self._ip_addresses:
            yield self.base_url.replace(self._PLACEHOLDER, str(ip))
