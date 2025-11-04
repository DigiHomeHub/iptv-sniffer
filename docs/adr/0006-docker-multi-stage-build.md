# ADR-0006: Docker Multi-Stage Build Strategy

**Related Tasks**: Task 8.1 – Docker Multi-Stage Build with Vue Frontend

## Context

We need a production-ready container image that bundles the FastAPI backend, Vue
frontend, and FFmpeg tooling. Early experiments that installed Node, Python
dependencies, and FFmpeg in a single stage produced bloated images (>800 MB) and
slow rebuilds. The repository already enforces that Vue builds emit assets into
`iptv_sniffer/web/static`, so any Docker solution must honour that output path
without requiring developers to pre-build assets.

## Decision

Adopt a three-stage Docker build:

1. **Frontend builder** (`node:20-alpine`) runs `npm ci` and builds the Vue
   bundle directly into `/app/iptv_sniffer/web/static`.
2. **Backend builder** (`python:3.12-slim`) installs application dependencies
   with `uv pip install --system --no-cache -r pyproject.toml`.
3. **Runtime image** (`python:3.12-slim`) installs FFmpeg, copies the prepared
   site-packages, static assets, and backend sources, and runs as a non-root
   `iptv` user under `uvicorn`.

Supporting assets include:

- `.dockerignore` to trim build context,
- `docker-compose.yml` for production-like runs,
- `docker-compose.dev.yml` with hot-reload backend and Node dev server, and
- helper scripts under `scripts/` for repeatable build/run flows.

## Consequences

- Image size stays below the 500 MB target while keeping FFmpeg available.
- Rebuilds reuse cached dependency layers for both npm and uv whenever manifests
  remain unchanged.
- Developers can rely on Compose to spin up both backend and Vite dev server
  without installing Node/FFmpeg locally.
- Docker integration tests require an environment with Docker installed; they
  remain opt-in via the `RUN_DOCKER_TESTS=1` guard.

## Alternatives Considered

- **Single-stage image**: Simpler Dockerfile but inflated size and slower builds.
- **Serving frontend via separate container**: Adds orchestration overhead and
  complicates deployment for a tool that benefits from an all-in-one image.
- **Copying pre-built assets**: Would require developers to run `npm run build`
  before `docker build`, hurting reproducibility.
