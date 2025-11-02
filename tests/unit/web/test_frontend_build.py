from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class TestFrontendBuild(unittest.TestCase):
    """Ensure Vue frontend scaffolding is configured correctly."""

    def setUp(self) -> None:
        self.frontend_dir = Path("frontend")

    def test_frontend_directory_exists(self) -> None:
        """Frontend directory should exist with package.json."""
        self.assertTrue(self.frontend_dir.exists(), "frontend/ directory missing")
        self.assertTrue(
            (self.frontend_dir / "package.json").exists(),
            "package.json missing in frontend/",
        )

    def test_vite_config_exists(self) -> None:
        """Vite configuration should be present."""
        vite_config = self.frontend_dir / "vite.config.ts"
        self.assertTrue(vite_config.exists(), "vite.config.ts missing")

    def test_vite_config_proxy_configured(self) -> None:
        """Vite should proxy API requests to FastAPI backend."""
        vite_config = self.frontend_dir / "vite.config.ts"
        content = vite_config.read_text()
        self.assertIn("proxy", content)
        self.assertIn("/api", content)
        self.assertIn("localhost:8000", content)

    def test_tailwind_css_configured(self) -> None:
        """Tailwind CSS should be properly configured."""
        tailwind_config = self.frontend_dir / "tailwind.config.js"
        self.assertTrue(tailwind_config.exists(), "tailwind.config.js missing")
        content = tailwind_config.read_text()
        self.assertIn("content", content)
        self.assertIn("./src/**/*", content)

    def test_frontend_build_succeeds(self) -> None:
        """Frontend build should complete without errors."""
        build_dir = Path("iptv_sniffer/web/static")
        if build_dir.exists():
            # Ensure directory cleaned between runs to avoid false positives.
            for item in build_dir.iterdir():
                if item.is_dir():
                    for sub in item.rglob("*"):
                        if sub.is_file():
                            sub.unlink()
                    item.rmdir()
                else:
                    item.unlink()

        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=self.frontend_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"npm run build failed with stderr:\n{result.stderr}",
        )
        self.assertTrue(
            (build_dir / "index.html").exists(),
            "Build did not produce static/index.html",
        )


if __name__ == "__main__":
    unittest.main()
