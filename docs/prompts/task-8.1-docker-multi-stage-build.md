# Task 8.1: Docker Multi-Stage Build with Vue Frontend

## Overview

Implement Docker multi-stage build that compiles Vue 3 frontend, Python backend, and FFmpeg into an optimized production image (<500MB).

**Priority**: P0 - Critical for deployment

**Estimated Duration**: 6-8 hours

## Prerequisites

- Task 7.0-7.5: Vue 3 + Vite Frontend (completed)
- Task 6.1-6.2: FastAPI Backend (completed)
- Task 2.1-2.3: FFmpeg Integration (completed)

## Design Context

**Multi-Stage Build Strategy**:

1. **Stage 1 (Frontend Builder)**: Compile Vue 3 + Vite → static files
2. **Stage 2 (Backend Builder)**: Install Python dependencies with uv
3. **Stage 3 (Final Runtime)**: Combine built assets, install FFmpeg, run as non-root

**Target Image Size**: <500MB (vs ~800MB naive approach)

**Performance Requirements**:

- Build time: <5 minutes (with cache)
- Startup time: <3 seconds
- Health check: responds within 2 seconds

## Implementation Summary

### Key Components

1. **Multi-Stage Dockerfile**

   - Frontend build stage (node:18-alpine)
   - Backend dependency stage (python:3.11-slim)
   - Final runtime stage (python:3.11-slim + FFmpeg)

2. **docker-compose.yml**

   - Development configuration with volume mounts
   - Production configuration with health checks
   - Environment variable management

3. **Docker Build Optimization**
   - Layer caching for npm and uv dependencies
   - .dockerignore to exclude dev files
   - Multi-arch support (amd64, arm64)

## TDD Implementation

### Test First (Red)

```bash
# tests/integration/test_docker_build.sh

#!/bin/bash
set -e

echo "Test 1: Docker image builds successfully"
docker build -t iptv-sniffer:test .
if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi
echo "✅ Docker build succeeded"

echo "Test 2: Image size < 500MB"
IMAGE_SIZE=$(docker images iptv-sniffer:test --format "{{.Size}}")
echo "Image size: $IMAGE_SIZE"
# Note: Manual verification required (docker images output varies by format)

echo "Test 3: Container starts successfully"
docker run -d --name iptv-test -p 8000:8000 iptv-sniffer:test
sleep 5
if ! docker ps | grep -q iptv-test; then
    echo "❌ Container failed to start"
    docker logs iptv-test
    docker rm -f iptv-test
    exit 1
fi
echo "✅ Container started"

echo "Test 4: Health check endpoint responds"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    docker logs iptv-test
    docker rm -f iptv-test
    exit 1
fi
echo "✅ Health check passed"

echo "Test 5: Static frontend files served"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Frontend not served (HTTP $HTTP_CODE)"
    docker logs iptv-test
    docker rm -f iptv-test
    exit 1
fi
echo "✅ Frontend served"

echo "Test 6: FFmpeg available in container"
docker exec iptv-test ffmpeg -version > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ FFmpeg not available"
    docker rm -f iptv-test
    exit 1
fi
echo "✅ FFmpeg available"

# Cleanup
docker rm -f iptv-test
docker rmi iptv-sniffer:test

echo "✅ All Docker integration tests passed"
```

```python
# tests/integration/test_docker_health.py

import unittest
import requests
import subprocess
import time

class TestDockerContainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start Docker container before tests"""
        subprocess.run(["docker", "build", "-t", "iptv-sniffer:test", "."], check=True)
        subprocess.run([
            "docker", "run", "-d",
            "--name", "iptv-test",
            "-p", "8001:8000",
            "iptv-sniffer:test"
        ], check=True)
        time.sleep(5)  # Wait for container startup

    @classmethod
    def tearDownClass(cls):
        """Stop and remove container after tests"""
        subprocess.run(["docker", "rm", "-f", "iptv-test"], check=False)
        subprocess.run(["docker", "rmi", "iptv-sniffer:test"], check=False)

    def test_health_endpoint(self):
        """Health check endpoint should return 200 OK"""
        response = requests.get("http://localhost:8001/health", timeout=5)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertIn("checks", data)

    def test_frontend_served(self):
        """Root path should serve Vue frontend"""
        response = requests.get("http://localhost:8001/", timeout=5)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])

    def test_api_endpoints_available(self):
        """API endpoints should be accessible"""
        response = requests.get("http://localhost:8001/docs", timeout=5)
        self.assertEqual(response.status_code, 200)
        self.assertIn("openapi", response.text.lower())

if __name__ == "__main__":
    unittest.main()
```

### Implement (Green)

#### Step 1: Create Multi-Stage Dockerfile

```dockerfile
# Dockerfile

# ============================================
# Stage 1: Build Vue 3 Frontend
# ============================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files for dependency caching
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies (cached if package files unchanged)
RUN npm ci --prefer-offline --no-audit

# Copy frontend source code
COPY frontend/ ./

# Build Vue 3 production bundle
RUN npm run build

# Output: /app/frontend/dist/ contains built static files


# ============================================
# Stage 2: Install Python Dependencies
# ============================================
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files for caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv pip install --system --no-cache -r pyproject.toml


# ============================================
# Stage 3: Final Runtime Image
# ============================================
FROM python:3.11-slim

# Install FFmpeg and clean up in single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-extra \
        curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy built Vue frontend to FastAPI static directory
COPY --from=frontend-builder /app/frontend/dist /app/iptv_sniffer/web/static

# Copy backend application code
COPY iptv_sniffer/ /app/iptv_sniffer/
COPY config/ /app/config/

# Create data directories
RUN mkdir -p /app/data /app/screenshots && \
    chmod 755 /app/data /app/screenshots

# Create non-root user for security
RUN useradd -m -u 1000 iptv && \
    chown -R iptv:iptv /app

# Switch to non-root user
USER iptv

# Expose web interface port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    SCREENSHOT_DIR=/app/screenshots

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI application
CMD ["uvicorn", "iptv_sniffer.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 2: Create .dockerignore

```.dockerignore
# .dockerignore

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
.testmondata

# Frontend
frontend/node_modules/
frontend/dist/
frontend/.vite/
frontend/coverage/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Git
.git/
.gitignore

# Documentation
docs/
*.md
!README.md

# Tests
tests/
*.test.ts
*.spec.ts

# CI/CD
.github/

# Development
.env.local
.env.development

# OS
.DS_Store
Thumbs.db
```

#### Step 3: Create docker-compose.yml

```yaml
# docker-compose.yml

version: "3.8"

services:
  iptv-sniffer:
    build:
      context: .
      dockerfile: Dockerfile
    image: iptv-sniffer:latest
    container_name: iptv-sniffer
    ports:
      - "8000:8000"
    volumes:
      # Persistent data storage
      - ./data:/app/data
      - ./screenshots:/app/screenshots
    environment:
      - MAX_CONCURRENCY=10
      - TIMEOUT=10
      - LOG_LEVEL=INFO
      - DATA_DIR=/app/data
      - SCREENSHOT_DIR=/app/screenshots
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
# Development override: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

```yaml
# docker-compose.dev.yml

version: "3.8"

services:
  iptv-sniffer:
    build:
      context: .
      dockerfile: Dockerfile
      target: backend-builder # Stop at backend builder for faster iteration
    volumes:
      # Mount source code for live reload
      - ./iptv_sniffer:/app/iptv_sniffer
      - ./frontend/dist:/app/iptv_sniffer/web/static
    command:
      [
        "uvicorn",
        "iptv_sniffer.web.app:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
      ]
    environment:
      - LOG_LEVEL=DEBUG
```

#### Step 4: Create Build and Run Scripts

```bash
# scripts/docker-build.sh

#!/bin/bash
set -e

echo "Building iptv-sniffer Docker image..."

# Build Vue frontend first (optional: can be part of Docker build)
echo "Building Vue frontend..."
cd frontend && npm ci && npm run build && cd ..

# Build Docker image
echo "Building Docker image..."
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -t iptv-sniffer:latest \
  -t iptv-sniffer:$(git rev-parse --short HEAD) \
  .

echo "Docker image built successfully!"
docker images iptv-sniffer:latest
```

```bash
# scripts/docker-run.sh

#!/bin/bash
set -e

echo "Starting iptv-sniffer container..."

docker run -d \
  --name iptv-sniffer \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/screenshots:/app/screenshots \
  -e MAX_CONCURRENCY=10 \
  -e TIMEOUT=10 \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  iptv-sniffer:latest

echo "Container started!"
echo "Access web interface at: http://localhost:8000"
echo "View logs: docker logs -f iptv-sniffer"
```

#### Step 5: Update Frontend Build Configuration

```typescript
// frontend/vite.config.ts (update build.outDir)

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },

  build: {
    // Output to FastAPI static directory
    outDir: "../iptv_sniffer/web/static",
    emptyOutDir: true,

    // Optimize for production
    minify: "esbuild",
    target: "es2020",

    rollupOptions: {
      output: {
        // Code splitting
        manualChunks: {
          "vue-vendor": ["vue", "vue-router"],
          "ui-vendor": ["@headlessui/vue"],
        },
      },
    },
  },

  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

### Verification Criteria

**Build Tests**:

- [ ] Docker image builds successfully in <5 minutes (cached)
- [ ] Final image size <500MB
- [ ] No security vulnerabilities (run `docker scan iptv-sniffer:latest`)
- [ ] Multi-arch build works (amd64, arm64)

**Runtime Tests**:

- [ ] Container starts in <3 seconds
- [ ] Health check endpoint responds 200 OK
- [ ] Frontend served at `http://localhost:8000/`
- [ ] API docs accessible at `http://localhost:8000/docs`
- [ ] FFmpeg available in container (`docker exec iptv-sniffer ffmpeg -version`)
- [ ] Non-root user (run `docker exec iptv-sniffer whoami` → should be `iptv`)

**Integration Tests**:

- [ ] Full scan workflow works (template mode)
- [ ] Screenshots captured and served
- [ ] M3U import/export works
- [ ] Data persists across container restarts (test with volumes)

**Performance Tests**:

- [ ] Initial page load <1 second (localhost)
- [ ] API response time <100ms (health check)
- [ ] Memory usage <256MB (idle), <512MB (scanning)

## Notes

**Development Workflow**:

1. **Local Development**: Run `npm run dev` in `frontend/` + `uvicorn` for backend separately
2. **Docker Development**: Use `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`
3. **Production Build**: Run `./scripts/docker-build.sh`

**Optimization Tips**:

- Layer caching: Place `COPY package.json` before `COPY frontend/` to cache npm install
- Build context: .dockerignore excludes unnecessary files (reduces context size by ~80%)
- Multi-stage build: Frontend builder and backend builder run in parallel (faster builds)

**Security Considerations**:

- Non-root user (UID 1000) prevents privilege escalation
- Health check ensures container liveness
- No secrets in image (use environment variables or Docker secrets)

## Dependencies

No new dependencies required. Uses existing:

- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+ (for local frontend builds)

## Related Tasks

- Task 7.0-7.5: Vue 3 frontend implementation
- Task 6.1-6.2: FastAPI backend implementation
- ADR-0007: Vue frontend framework decision
- ADR-0006: Docker multi-stage build architecture (if exists)
