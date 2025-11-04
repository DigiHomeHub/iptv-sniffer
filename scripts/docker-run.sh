#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${IMAGE_TAG:-iptv-sniffer:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-iptv-sniffer}"

if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
  echo "Container ${CONTAINER_NAME} already exists. Stopping and removing..."
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

mkdir -p data screenshots

echo "Starting container ${CONTAINER_NAME} from image ${IMAGE_TAG}"
docker run -d \
  --name "${CONTAINER_NAME}" \
  -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/screenshots:/app/screenshots" \
  -e MAX_CONCURRENCY=10 \
  -e TIMEOUT=10 \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  "${IMAGE_TAG}"

echo "Container started. Web UI available at http://localhost:8000"
echo "View logs with: docker logs -f ${CONTAINER_NAME}"
