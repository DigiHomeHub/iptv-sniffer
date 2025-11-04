#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="iptv-sniffer:test"
CONTAINER_NAME="iptv-sniffer-test"

echo "### Building Docker image (${IMAGE_TAG})"
docker build -t "${IMAGE_TAG}" .

echo "### Verifying image size"
IMAGE_SIZE=$(docker images "${IMAGE_TAG}" --format "{{.Size}}")
echo "Image size: ${IMAGE_SIZE}"

echo "### Starting container"
docker run -d --rm --name "${CONTAINER_NAME}" -p 8000:8000 "${IMAGE_TAG}"

echo "Waiting for container to become healthy..."
sleep 5

echo "### Health check"
curl -fsS http://localhost:8000/health > /dev/null

echo "### Frontend availability"
curl -fsS http://localhost:8000/ > /dev/null

echo "### FFmpeg check"
docker exec "${CONTAINER_NAME}" ffmpeg -version > /dev/null

echo "### Cleaning up"
docker rm -f "${CONTAINER_NAME}" > /dev/null
docker rmi "${IMAGE_TAG}" > /dev/null

echo "All Docker integration tests passed."
