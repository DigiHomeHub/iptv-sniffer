#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="${IMAGE_TAG:-iptv-sniffer:latest}"

echo ">>> Building Vue frontend bundle"
(cd "${REPO_ROOT}/frontend" && npm ci && npm run build)

echo ">>> Building Docker image ${IMAGE_TAG}"
docker build \
  --build-arg BUILD_DATE="$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --build-arg VCS_REF="$(git -C "${REPO_ROOT}" rev-parse --short HEAD)" \
  -t "${IMAGE_TAG}" \
  "${REPO_ROOT}"

echo ">>> Docker image built successfully:"
docker images "${IMAGE_TAG}"
