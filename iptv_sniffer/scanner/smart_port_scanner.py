from __future__ import annotations

import logging
from typing import AsyncIterator, List, Protocol, Sequence, Set, Tuple

from .multicast_strategy import MulticastScanStrategy
from .validator import StreamValidationResult

logger = logging.getLogger(__name__)


class StreamValidatorProtocol(Protocol):
    """Protocol for stream validators used by scanner."""

    async def validate(self, url: str, timeout: int = 10) -> StreamValidationResult: ...


class SmartPortScanner:
    """
    Smart multicast port scanner that minimises validation workload.

    The scanner first probes the full port list on the initial multicast IP to
    identify active services. Discovered ports are then reused for the remainder
    of the IP range to avoid redundant validations.
    """

    def __init__(
        self,
        strategy: MulticastScanStrategy,
        validator: StreamValidatorProtocol,
        *,
        enable_smart_scan: bool = True,
        discovery_timeout: int | None = 20,
    ) -> None:
        self._strategy = strategy
        self._validator = validator
        self._enable_smart_scan = enable_smart_scan
        self._discovery_timeout = discovery_timeout

    async def scan(self) -> AsyncIterator[StreamValidationResult]:
        """
        Execute smart multicast scanning.

        Yields:
            StreamValidationResult objects for each validated stream.
        """
        ip_addresses = [str(address) for address in self._strategy.iter_ip_addresses()]
        if not ip_addresses:
            logger.info("SmartPortScanner: no multicast addresses to scan.")
            return

        if not self._enable_smart_scan or len(ip_addresses) == 1:
            async for result in self._scan_ips(ip_addresses, self._strategy.ports):
                yield result
            return

        first_ip, *remaining_ips = ip_addresses
        discovered_ports, discovery_results = await self._discover_ports_on_first_ip(
            first_ip
        )
        for result in discovery_results:
            yield result

        if not remaining_ips:
            logger.debug("SmartPortScanner: single multicast IP processed.")
            return

        if not discovered_ports:
            logger.warning(
                "SmartPortScanner: no ports discovered on %s; falling back to full scan.",
                first_ip,
            )
            async for result in self._scan_ips(remaining_ips, self._strategy.ports):
                yield result
            return

        async for result in self._scan_ips(remaining_ips, sorted(discovered_ports)):
            yield result

    async def _discover_ports_on_first_ip(
        self, ip_address: str
    ) -> Tuple[Set[int], List[StreamValidationResult]]:
        discovered_ports: Set[int] = set()
        results: List[StreamValidationResult] = []

        for port in self._strategy.ports:
            url = self._build_url(ip_address, port)
            timeout = self._discovery_timeout if self._discovery_timeout else None
            if timeout is None:
                result = await self._validator.validate(url)
            else:
                result = await self._validator.validate(url, timeout=timeout)
            results.append(result)
            if result.is_valid:
                discovered_ports.add(port)

        logger.debug(
            "SmartPortScanner: discovered ports %s on %s",
            sorted(discovered_ports),
            ip_address,
        )
        return discovered_ports, results

    async def _scan_ips(
        self, ip_addresses: Sequence[str], ports: Sequence[int]
    ) -> AsyncIterator[StreamValidationResult]:
        for ip_address in ip_addresses:
            for port in ports:
                url = self._build_url(ip_address, port)
                yield await self._validator.validate(url)

    def _build_url(self, ip_address: str, port: int) -> str:
        return f"{self._strategy.protocol}://{ip_address}:{port}"
