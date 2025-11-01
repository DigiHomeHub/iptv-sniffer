# Task 6.1: FastAPI Setup

## Task Overview

**Phase**: 6 - Web API  
**Duration**: 2-3 hours  
**Complexity**: Low-Medium

**Goal**: Initialize FastAPI application with CORS, health check, and OpenAPI documentation.

**Success Criteria**:

- [ ] All tests pass (TestClient)
- [ ] Type checking passes (uv run pyrefly check)
- [ ] Test coverage ≥ 75%

---

## Design Context

**FastAPI Selection** (Design.md Section 1, lines 233-265):

- Native async/await for I/O-bound operations
- Automatic Pydantic request/response validation
- Auto-generated OpenAPI/Swagger docs
- Background task support

---

## Prerequisites

- [x] Task 2.1: FFmpeg Availability Check (for health endpoint)

### Dependencies

```bash
uv add fastapi uvicorn
```

---

## Implementation

**File**: `iptv_sniffer/web/app.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from iptv_sniffer import __version__
from iptv_sniffer.utils.ffmpeg import check_ffmpeg_installed

app = FastAPI(
    title="iptv-sniffer",
    description="Discover and validate IPTV channels on local networks",
    version=__version__
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting iptv-sniffer v{__version__}")
    if not check_ffmpeg_installed():
        logger.error("FFmpeg not found")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": __version__,
        "checks": {
            "ffmpeg": check_ffmpeg_installed()
        }
    }
```

---

## Testing

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_openapi_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200
```

---

## Commit

```bash
git commit -m "feat(web): initialize FastAPI application with health check

- Add FastAPI app with CORS middleware
- Implement health check endpoint with FFmpeg status
- Configure OpenAPI documentation
- Add startup event for initialization
- Include 3 integration tests with 80% coverage

Foundation for REST API and WebSocket support

Closes #<issue-number>"
```
