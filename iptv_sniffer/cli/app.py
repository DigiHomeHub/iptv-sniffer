"""Typer-based command-line interface for iptv-sniffer."""

from __future__ import annotations

from typing import Optional

import typer

from iptv_sniffer import __version__

app = typer.Typer(
    name="iptv-sniffer",
    add_completion=False,
    help="Discover, validate, and export IPTV channels from your local network.",
    no_args_is_help=True,
)


def version_callback(value: Optional[bool]) -> None:
    """Display the package version when --version is provided."""
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def _notify_not_implemented(command: str) -> None:
    """Emit a consistent placeholder message for unimplemented commands."""
    typer.secho(
        f"{command} command not yet implemented",
        fg=typer.colors.YELLOW,
    )
    raise typer.Exit(code=1)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the iptv-sniffer version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    Manage IPTV discovery, validation, and export workflows.

    Global options are configured here; subcommands implement the individual
    features.
    """


@app.command()
def scan() -> None:
    """
    Start a network scan to discover IPTV channels.

    This placeholder will be replaced in Phase 3 with async scanning logic.
    """
    _notify_not_implemented("scan")


@app.command()
def validate() -> None:
    """
    Validate discovered channels to ensure stream availability.

    Phase 4 will extend this command with FFmpeg powered validation routines.
    """
    _notify_not_implemented("validate")


@app.command()
def export() -> None:
    """
    Export managed channels to an M3U playlist.

    Future phases will wire this into the M3U generator module.
    """
    _notify_not_implemented("export")


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    app()
