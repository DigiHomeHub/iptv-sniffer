# Task 6.2: Scan Endpoints

## Task Overview

**Phase**: 6 - Web API  
**Duration**: 4-5 hours  
**Complexity**: High

**Goal**: Implement REST API endpoints for scan operations (start, status, cancel) with background task execution.

**Success Criteria**:

- [ ] All tests pass (TestClient with async)
- [ ] Type checking passes (mypy --strict)
- [ ] Test coverage ≥ 75%
- [ ] Module size < 500 lines

---

## Design Context

**REST API Design** (Design.md Section 8, lines 656-733):

- `POST /api/scan/start`: Start scan with mode selection
- `GET /api/scan/{scan_id}`: Get scan status
- `DELETE /api/scan/{scan_id}`: Cancel scan
- Background task execution via FastAPI BackgroundTasks

---

## Prerequisites

- [x] Task 6.1: FastAPI Setup
- [x] Task 3.4: Scan Orchestrator
- [x] Task 3.2: Template Scan Strategy
- [x] Task 5.1: Multicast Scan Strategy

---

## Implementation

**File**: `iptv_sniffer/web/api/scan.py`

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
from uuid import uuid4
from iptv_sniffer.scanner.strategy import ScanMode
from iptv_sniffer.scanner.template_strategy import TemplateScanStrategy
from iptv_sniffer.scanner.multicast_strategy import MulticastScanStrategy
from iptv_sniffer.scanner.validator import StreamValidator
from iptv_sniffer.scanner.orchestrator import ScanOrchestrator

router = APIRouter(prefix="/api/scan", tags=["scan"])

# Global scan registry
active_scans: Dict[str, dict] = {}

class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

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

@router.post("/start")
async def start_scan(request: ScanStartRequest, background_tasks: BackgroundTasks):
    scan_id = str(uuid4())

    # Create strategy based on mode
    if request.mode == ScanMode.TEMPLATE:
        strategy = TemplateScanStrategy(
            base_url=request.base_url,
            start_ip=request.start_ip,
            end_ip=request.end_ip
        )
    elif request.mode == ScanMode.MULTICAST:
        strategy = MulticastScanStrategy(
            protocol=request.protocol,
            ip_ranges=request.ip_ranges,
            ports=request.ports
        )
    else:
        raise HTTPException(400, f"Unsupported mode: {request.mode}")

    # Register scan
    active_scans[scan_id] = {
        "status": ScanStatus.PENDING,
        "progress": 0,
        "total": strategy.estimate_target_count(),
        "valid": 0,
        "invalid": 0,
        "started_at": datetime.utcnow()
    }

    # Start background task
    background_tasks.add_task(execute_scan, scan_id, strategy)

    return {"scan_id": scan_id, "status": ScanStatus.PENDING}

@router.get("/{scan_id}")
async def get_scan_status(scan_id: str):
    if scan_id not in active_scans:
        raise HTTPException(404, "Scan not found")
    return active_scans[scan_id]

@router.delete("/{scan_id}")
async def cancel_scan(scan_id: str):
    if scan_id not in active_scans:
        raise HTTPException(404, "Scan not found")
    active_scans[scan_id]["status"] = ScanStatus.CANCELLED
    return {"cancelled": True}

async def execute_scan(scan_id: str, strategy):
    """Execute scan in background"""
    try:
        active_scans[scan_id]["status"] = ScanStatus.RUNNING
        validator = StreamValidator(max_workers=10)
        orchestrator = ScanOrchestrator(validator, max_concurrency=10)

        async for result in orchestrator.execute_scan(strategy):
            scan_data = active_scans[scan_id]
            scan_data["progress"] += 1
            scan_data["valid"] += 1 if result.is_valid else 0
            scan_data["invalid"] += 1 if not result.is_valid else 0

            if scan_data["status"] == ScanStatus.CANCELLED:
                return

        active_scans[scan_id]["status"] = ScanStatus.COMPLETED
        active_scans[scan_id]["completed_at"] = datetime.utcnow()
    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}")
        active_scans[scan_id]["status"] = ScanStatus.FAILED
```

**Register Router** in `app.py`:

```python
from iptv_sniffer.web.api import scan
app.include_router(scan.router)
```

---

## Commit

```bash
git commit -m "feat(web): implement scan REST API endpoints

- Add POST /api/scan/start with mode selection (template/multicast)
- Implement GET /api/scan/{scan_id} for status tracking
- Add DELETE /api/scan/{scan_id} for cancellation
- Background scan execution via FastAPI BackgroundTasks
- Support both TemplateScanStrategy and MulticastScanStrategy
- Include 6 integration tests with 78% coverage

Implements Design.md Section 8 REST API design

Closes #<issue-number>"
```

---

## Next Steps

**Phase 6 Web API complete!**

Remaining phases (not in current prompt set):

- Phase 7: Web Interface (HTML/CSS/JS)
- Phase 8: Docker & Deployment
- Phase 9: Polish & Release

---

## All Task Prompts Complete

**Summary**: 22 task prompts created across 6 phases:

- Phase 1 (Core Infrastructure): 4 tasks
- Phase 2 (FFmpeg Integration): 3 tasks
- Phase 3 (Network Scanning): 4 tasks
- Phase 4 (M3U Support): 3 tasks
- Phase 5 (Multicast Support): 3 tasks
- Phase 6 (Web API): 2 tasks

Each prompt provides:

- TDD workflow (Red-Green-Refactor)
- Design context from Design.md
- Type signatures and implementation guidance
- Quality gates and verification steps
- Conventional commit message templates
