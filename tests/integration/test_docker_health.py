from __future__ import annotations

import os
import shutil
import subprocess
import time
import unittest

import requests


RUN_DOCKER_TESTS = os.environ.get("RUN_DOCKER_TESTS") == "1"
DOCKER_AVAILABLE = shutil.which("docker") is not None


@unittest.skipUnless(
    RUN_DOCKER_TESTS and DOCKER_AVAILABLE, "Docker integration tests disabled"
)
class TestDockerContainer(unittest.TestCase):
    """Integration tests that exercise the Docker image runtime."""

    image_tag = os.environ.get("IPTV_IMAGE_TAG", "iptv-sniffer:test-health")
    container_name = os.environ.get("IPTV_CONTAINER_NAME", "iptv-sniffer-health")
    host_port = int(os.environ.get("IPTV_HOST_PORT", "8002"))

    @classmethod
    def setUpClass(cls) -> None:
        cls._run(["docker", "build", "-t", cls.image_tag, "."])
        cls._run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--name",
                cls.container_name,
                "-p",
                f"{cls.host_port}:8000",
                cls.image_tag,
            ]
        )
        time.sleep(6)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._run(["docker", "rm", "-f", cls.container_name], check=False)
        cls._run(["docker", "rmi", cls.image_tag], check=False)

    @classmethod
    def _run(
        cls, command: list[str], check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(command, check=check, text=True, capture_output=True)

    def test_health_endpoint(self) -> None:
        response = requests.get(f"http://localhost:{self.host_port}/health", timeout=5)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("status", body)
        self.assertIn("version", body)

    def test_frontend_served(self) -> None:
        response = requests.get(f"http://localhost:{self.host_port}/", timeout=5)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    def test_openapi_available(self) -> None:
        response = requests.get(f"http://localhost:{self.host_port}/docs", timeout=5)
        self.assertEqual(response.status_code, 200)
        self.assertIn("openapi", response.text.lower())


if __name__ == "__main__":
    unittest.main()
