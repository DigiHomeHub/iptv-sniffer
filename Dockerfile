# syntax=docker/dockerfile:1.7

###############################################
# Stage 1: Build Vue frontend assets
###############################################
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies with caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --prefer-offline --no-audit

# Copy application sources and ensure expected output directory exists
COPY frontend/ ./
RUN mkdir -p /app/iptv_sniffer/web/static

# Build production bundle (outputs to ../iptv_sniffer/web/static)
RUN npm run build


###############################################
# Stage 2: Install Python dependencies with uv
###############################################
FROM python:3.12-slim AS backend-builder

ENV UV_SYSTEM_PIP=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

# Copy dependency definitions separately for caching
COPY pyproject.toml uv.lock ./

# Install project dependencies into the system environment
RUN uv pip install --system --no-cache -r pyproject.toml


###############################################
# Stage 3: Final runtime image
###############################################
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="iptv-sniffer" \
      org.opencontainers.image.description="Discover and validate IPTV channels on local networks." \
      org.opencontainers.image.source="https://github.com/DigiHomeHub/iptv-sniffer" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    SCREENSHOT_DIR=/app/screenshots

WORKDIR /app

# Install FFmpeg and runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application source
COPY iptv_sniffer/ /app/iptv_sniffer/
COPY config/ /app/config/
COPY pyproject.toml README.md /app/

# Copy built frontend assets into FastAPI static directory
COPY --from=frontend-builder /app/iptv_sniffer/web/static /app/iptv_sniffer/web/static

# Create application user and directories
RUN mkdir -p "${DATA_DIR}" "${SCREENSHOT_DIR}" && \
    adduser --disabled-password --gecos "" --home /home/iptv iptv && \
    chown -R iptv:iptv /app

USER iptv

EXPOSE 8000

# Healthcheck ensures the application stays responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "iptv_sniffer.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
