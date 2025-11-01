from __future__ import annotations

import ipaddress
from typing import AsyncIterator, Iterable, List, Sequence, Tuple

from .strategy import ScanStrategy


class MulticastScanStrategy(ScanStrategy):
    """Scan strategy that enumerates multicast RTP/UDP stream endpoints."""

    _SUPPORTED_PROTOCOLS = {"udp", "rtp"}

    def __init__(
        self,
        *,
        protocol: str,
        ip_ranges: Sequence[str],
        ports: Sequence[int],
    ) -> None:
        if protocol.lower() not in self._SUPPORTED_PROTOCOLS:
            raise ValueError(
                f"Unsupported protocol '{protocol}'. "
                f"Supported multicast protocols: {sorted(self._SUPPORTED_PROTOCOLS)}"
            )
        if not ip_ranges:
            raise ValueError("At least one multicast IP range must be provided.")
        if not ports:
            raise ValueError(
                "At least one port must be provided for multicast scanning."
            )

        self._protocol = protocol.lower()
        self._ranges: List[Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]] = [
            self._parse_range(range_definition) for range_definition in ip_ranges
        ]
        self._ports: Tuple[int, ...] = tuple(
            self._validate_port(port) for port in ports
        )

    @property
    def protocol(self) -> str:
        """Return multicast protocol identifier (udp or rtp)."""
        return self._protocol

    @property
    def ports(self) -> Tuple[int, ...]:
        """Return tuple of configured ports."""
        return self._ports

    async def generate_targets(self) -> AsyncIterator[str]:
        """Yield multicast targets for validation."""
        for start, end in self._ranges:
            for address in self._iterate_range(start, end):
                for port in self._ports:
                    yield f"{self._protocol}://{address}:{port}"

    def estimate_target_count(self) -> int:
        """Estimate total multicast targets to be generated."""
        ip_total = sum(self._count_ips(start, end) for start, end in self._ranges)
        return ip_total * len(self._ports)

    def iter_ip_addresses(self) -> Iterable[ipaddress.IPv4Address]:
        """Iterate over multicast IP addresses represented by configured ranges."""
        for start, end in self._ranges:
            yield from self._iterate_range(start, end)

    @staticmethod
    def _parse_range(
        range_definition: str,
    ) -> Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]:
        try:
            if "-" in range_definition:
                start_raw, end_raw = [
                    part.strip() for part in range_definition.split("-", 1)
                ]
                start = ipaddress.IPv4Address(start_raw)
                end = ipaddress.IPv4Address(end_raw)
            else:
                start = end = ipaddress.IPv4Address(range_definition.strip())
        except ipaddress.AddressValueError as exc:
            raise ValueError(
                f"Invalid multicast IP range '{range_definition}'."
            ) from exc

        if int(start) > int(end):
            raise ValueError(
                f"Multicast IP range start must be <= end: '{range_definition}'."
            )

        if not (start.is_multicast and end.is_multicast):
            raise ValueError(
                f"IP range '{range_definition}' must be within the multicast block (224.0.0.0/4)."
            )

        return start, end

    @staticmethod
    def _iterate_range(
        start: ipaddress.IPv4Address, end: ipaddress.IPv4Address
    ) -> Iterable[ipaddress.IPv4Address]:
        start_int = int(start)
        end_int = int(end)
        for value in range(start_int, end_int + 1):
            yield ipaddress.IPv4Address(value)

    @staticmethod
    def _count_ips(start: ipaddress.IPv4Address, end: ipaddress.IPv4Address) -> int:
        return int(end) - int(start) + 1

    @staticmethod
    def _validate_port(port: int) -> int:
        if not (1 <= int(port) <= 65535):
            raise ValueError(f"Port '{port}' is out of valid range (1-65535).")
        return int(port)
