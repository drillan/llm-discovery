"""Export command for multi-format export."""

from collections.abc import Callable
from pathlib import Path

import typer

from llm_discovery.cli.output import console, display_error
from llm_discovery.constants import SUPPORTED_EXPORT_FORMATS
from llm_discovery.exceptions import CacheNotFoundError
from llm_discovery.models import Model
from llm_discovery.models.config import Config
from llm_discovery.services.discovery import DiscoveryService
from llm_discovery.services.exporters import (
    export_csv,
    export_json,
    export_markdown,
    export_toml,
    export_yaml,
)


def export_command(
    format: str = typer.Option(
        ...,
        "--format",
        help=f"Export format ({', '.join(SUPPORTED_EXPORT_FORMATS)})",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Output file path (stdout if not specified)",
    ),
) -> None:
    """Export model data to various formats.

    Supports JSON, CSV, YAML, Markdown, and TOML formats.
    Data is exported from the local cache.
    """
    try:
        # Validate format
        if format not in SUPPORTED_EXPORT_FORMATS:
            display_error(
                f"Unsupported format '{format}'.",
                f"Available formats: {', '.join(SUPPORTED_EXPORT_FORMATS)}",
            )
            raise typer.Exit(2)

        # Load configuration (API keys not required for reading cache)
        try:
            config = Config.from_env(require_api_keys=False)
        except ValueError as e:
            display_error("Configuration error", str(e))
            raise typer.Exit(1)

        service = DiscoveryService(config)

        # Get models from cache
        try:
            models = service.get_cached_models()
        except CacheNotFoundError:
            display_error(
                "No cached data available.",
                "Please run 'llm-discovery list' first to fetch model data.",
            )
            raise typer.Exit(1)

        if not models:
            display_error("No models found in cache.")
            raise typer.Exit(1)

        # Export based on format
        exporters: dict[str, Callable[[list[Model]], str]] = {
            "json": export_json,
            "csv": export_csv,
            "yaml": export_yaml,
            "markdown": export_markdown,
            "toml": export_toml,
        }

        try:
            exported_data = exporters[format](models)
        except ValueError as e:
            display_error(f"Export failed: {str(e)}")
            raise typer.Exit(1)

        # Write to output
        if output:
            try:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(exported_data, encoding="utf-8")
                console.print(
                    f"[green]Exported {len(models)} models to {output} ({format.upper()} format)[/green]"
                )
            except OSError as e:
                display_error(
                    f"Failed to write to file '{output}'.",
                    f"Cause: {str(e)}\n\n"
                    "Suggested actions:\n"
                    "  1. Check directory permissions\n"
                    "  2. Ensure the directory exists\n"
                    "  3. Try writing to a different location",
                )
                raise typer.Exit(1)
        else:
            # Write to stdout
            console.print(exported_data, end="")

    except ValueError as e:
        display_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
