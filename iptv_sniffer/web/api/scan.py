from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Protocol
from uuid import uuid4

import contextlib
from enum import Enum

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from iptv_sniffer.scanner.multicast_strategy import MulticastScanStrategy
from iptv_sniffer.scanner.orchestrator import ScanOrchestrator
from iptv_sniffer.scanner.presets import PresetLoader, ScanPreset
from iptv_sniffer.scanner.strategy import ScanMode, ScanStrategy
from iptv_sniffer.scanner.template_strategy import TemplateScanStrategy
from iptv_sniffer.scanner.validator import StreamValidationResult, StreamValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scan", tags=["scan"])


class ScanOrchestratorProtocol(Protocol):
    """Protocol for scan orchestrator interface."""

    def execute_scan(
        self, strategy: ScanStrategy
    ) -> AsyncIterator[StreamValidationResult]:
        """Execute scan strategy and yield validation results."""
        ...


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class ScanSession:
    scan_id: str
    strategy: ScanStrategy
    status: ScanStatus = ScanStatus.PENDING
    progress: int = 0
    total: int = 0
    valid: int = 0
    invalid: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    task: Optional[asyncio.Task[Any]] = None
    timeout: int = 10


class ScanStartRequest(BaseModel):
    mode: ScanMode
    base_url: Optional[str] = None
    start_ip: Optional[str] = None
    end_ip: Optional[str] = None
    protocol: Optional[str] = None
    ip_ranges: Optional[List[str]] = None
    ports: Optional[List[int]] = None
    preset: Optional[str] = None
    timeout: int = Field(default=10, ge=1, le=60)

    @field_validator("ports", mode="before")
    @classmethod
    def validate_port(cls, value: Optional[List[int]]) -> Optional[List[int]]:
        if value is None:
            return None
        validated: List[int] = []
        for port in value:
            if port is None:
                raise ValueError("Ports must be integers.")
            if not (1 <= port <= 65535):
                raise ValueError("Ports must be within range 1-65535.")
            validated.append(port)
        return validated


class ScanStartResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    total: int


class ScanStatusResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    progress: int
    total: int
    valid: int
    invalid: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ScanCancelResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    cancelled: bool


class ScanNotFoundError(Exception):
    """Raised when a scan identifier does not correspond to active session."""


DEFAULT_PRESET_PATH = (
    Path(__file__).resolve().parents[4] / "config" / "multicast_presets.json"
)


class ScanManager:
    """Coordinate scan lifecycle and background execution."""

    def __init__(
        self,
        preset_loader: Optional[PresetLoader] = None,
        orchestrator_factory: Optional[Callable[[], ScanOrchestratorProtocol]] = None,
    ) -> None:
        self._sessions: Dict[str, ScanSession] = {}
        self._lock = asyncio.Lock()
        self._preset_loader = preset_loader or PresetLoader(DEFAULT_PRESET_PATH)
        self._orchestrator_factory = (
            orchestrator_factory or self._default_orchestrator_factory
        )

    async def start_scan(
        self,
        request: ScanStartRequest,
        timeout: int,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> ScanSession:
        strategy = self._build_strategy_from_request(request)
        total = _safe_estimate_total(strategy)
        session = ScanSession(
            scan_id=str(uuid4()),
            strategy=strategy,
            total=total,
            timeout=timeout,
        )

        async with self._lock:
            self._sessions[session.scan_id] = session

        task = asyncio.create_task(self._run_scan(session))
        session.task = task

        if background_tasks is not None:
            background_tasks.add_task(self._finalize_task, task)

        logger.info(
            "Started scan %s using mode %s", session.scan_id, request.mode.value
        )
        return session

    async def get_scan(self, scan_id: str) -> ScanSession:
        async with self._lock:
            try:
                return self._sessions[scan_id]
            except KeyError as exc:
                raise ScanNotFoundError from exc

    async def cancel_scan(self, scan_id: str) -> ScanSession:
        async with self._lock:
            if scan_id not in self._sessions:
                raise ScanNotFoundError
            session = self._sessions[scan_id]
            session.cancel_event.set()
            session.status = ScanStatus.CANCELLED
        if session.task and not session.task.done():
            session.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await session.task
        session.completed_at = datetime.now(timezone.utc)
        logger.info("Cancelled scan %s", scan_id)
        return session

    async def _run_scan(self, session: ScanSession) -> None:
        orchestrator = self._orchestrator_factory()
        session.status = ScanStatus.RUNNING
        try:
            async for result in orchestrator.execute_scan(session.strategy):
                await self._handle_result(session, result)
                if session.cancel_event.is_set():
                    session.status = ScanStatus.CANCELLED
                    session.completed_at = datetime.now(timezone.utc)
                    return
            session.status = ScanStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc)
        except asyncio.CancelledError:
            session.status = ScanStatus.CANCELLED
            session.completed_at = datetime.now(timezone.utc)
            raise
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Scan %s failed", session.scan_id)
            session.status = ScanStatus.FAILED
            session.error = str(exc)
            session.completed_at = datetime.now(timezone.utc)

    async def _handle_result(
        self, session: ScanSession, result: StreamValidationResult
    ) -> None:
        session.progress += 1
        if result.is_valid:
            session.valid += 1
        else:
            session.invalid += 1

    async def _finalize_task(self, task: asyncio.Task[Any]) -> None:
        try:
            await task
        except asyncio.CancelledError:
            pass

    def _build_strategy_from_request(self, request: ScanStartRequest) -> ScanStrategy:
        if request.mode == ScanMode.TEMPLATE:
            base_url = request.base_url
            start_ip = request.start_ip
            end_ip = request.end_ip
            if base_url is None or start_ip is None or end_ip is None:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Template scan requires base_url, start_ip, and end_ip.",
                )
            return TemplateScanStrategy(
                base_url=base_url,
                start_ip=start_ip,
                end_ip=end_ip,
            )

        if request.mode == ScanMode.MULTICAST:
            if request.preset:
                preset = self._load_preset(request.preset)
                return preset.to_strategy()
            protocol = request.protocol
            ip_ranges = request.ip_ranges
            ports = request.ports
            if protocol is None or ip_ranges is None or ports is None:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Multicast scan requires protocol, ip_ranges, and ports or preset.",
                )
            return MulticastScanStrategy(
                protocol=protocol,
                ip_ranges=ip_ranges,
                ports=ports,
            )

        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=f"Unsupported scan mode: {request.mode}"
        )

    def _load_preset(self, preset_id: str) -> ScanPreset:
        preset = self._preset_loader.get_by_id(preset_id)
        if not preset:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"Preset '{preset_id}' not found.",
            )
        return preset

    @staticmethod
    def _default_orchestrator_factory() -> ScanOrchestrator:
        validator = StreamValidator(max_workers=10)
        return ScanOrchestrator(validator, max_concurrency=10)


def _safe_estimate_total(strategy: ScanStrategy) -> int:
    try:
        return strategy.estimate_target_count()
    except Exception:  # pylint: disable=broad-except
        logger.warning("Failed to estimate target count for strategy %s", strategy)
        return 0


scan_manager = ScanManager()


@router.post(
    "/start",
    response_model=ScanStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_scan(
    request: ScanStartRequest,
    background_tasks: BackgroundTasks,
) -> ScanStartResponse:
    session = await scan_manager.start_scan(
        request, timeout=request.timeout, background_tasks=background_tasks
    )
    return ScanStartResponse(
        scan_id=session.scan_id, status=session.status, total=session.total
    )


@router.get(
    "/{scan_id}",
    response_model=ScanStatusResponse,
)
async def get_scan(scan_id: str) -> ScanStatusResponse:
    try:
        session = await scan_manager.get_scan(scan_id)
    except ScanNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Scan not found"
        ) from None
    return ScanStatusResponse(
        scan_id=session.scan_id,
        status=session.status,
        progress=session.progress,
        total=session.total,
        valid=session.valid,
        invalid=session.invalid,
        started_at=session.started_at,
        completed_at=session.completed_at,
        error=session.error,
    )


@router.delete(
    "/{scan_id}",
    response_model=ScanCancelResponse,
)
async def cancel_scan(scan_id: str) -> ScanCancelResponse:
    try:
        session = await scan_manager.cancel_scan(scan_id)
    except ScanNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Scan not found"
        ) from None
    return ScanCancelResponse(
        scan_id=session.scan_id,
        status=session.status,
        cancelled=session.status == ScanStatus.CANCELLED,
    )
