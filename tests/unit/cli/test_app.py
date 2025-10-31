from __future__ import annotations

import unittest

from typer.testing import CliRunner

from iptv_sniffer import __version__
from iptv_sniffer.cli.app import app


class TestCliApp(unittest.TestCase):
    """Ensure the CLI is wired up via Typer."""

    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_cli_version_command(self) -> None:
        """--version should display package version."""
        result = self.runner.invoke(app, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(__version__, result.stdout)

    def test_cli_help_command_lists_subcommands(self) -> None:
        """Main help should list available subcommands."""
        result = self.runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        for command in ("scan", "validate", "export"):
            with self.subTest(command=command):
                self.assertIn(command, result.stdout)

    def test_cli_subcommand_help(self) -> None:
        """Each subcommand should expose help output."""
        for command in ("scan", "validate", "export"):
            with self.subTest(command=command):
                result = self.runner.invoke(app, [command, "--help"])
                self.assertEqual(result.exit_code, 0)
                self.assertIn("Usage", result.stdout)

    def test_cli_placeholder_commands_notify_not_implemented(self) -> None:
        """Placeholder commands should inform users they are not implemented."""
        expected_messages = {
            "scan": "scan command not yet implemented",
            "validate": "validate command not yet implemented",
            "export": "export command not yet implemented",
        }
        for command, message in expected_messages.items():
            with self.subTest(command=command):
                result = self.runner.invoke(app, [command])
                self.assertEqual(result.exit_code, 1)
                self.assertIn(message, result.stdout)
