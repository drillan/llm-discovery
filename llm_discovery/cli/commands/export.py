"""Export command for multi-format export."""

from collections.abc import Callable
from pathlib import Path

import typer

from llm_discovery.cli.output import console, display_error
from llm_discovery.constants import SUPPORTED_EXPORT_FORMATS
from llm_discovery.exceptions import CacheCorruptedError
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

        # FR-001: Explicit data source selection (cache or prebuilt)
        cache_file = config.llm_discovery_cache_dir / "models_cache.toml"
        has_cache = cache_file.exists()
        has_prebuilt = service.prebuilt_loader.is_available()

        if has_cache:
            try:
                models = service.get_cached_models()
            except CacheCorruptedError as e:
                display_error(
                    "Cache file is corrupted.",
                    f"Error: {e}\n\n"
                    "Please run 'llm-discovery update' to refresh the cache.",
                )
                raise typer.Exit(1)
        elif has_prebuilt:
            # Use prebuilt data when cache not available
            models = service.prebuilt_loader.load_models()
        else:
            display_error(
                "No data available.",
                "Please configure API keys and run 'llm-discovery update' to fetch model data.",
            )
            raise typer.Exit(1)

        if not models:
            display_error("No models found in cache.")
            raise typer.Exit(1)

        # Get data source info
        try:
            data_source_info = service.get_data_source_info()
        except Exception:
            data_source_info = None

        # Export based on format
        exporters: dict[str, Callable[[list[Model]], str]] = {
            "json": lambda m: export_json(m, data_source_info=data_source_info),
            "csv": lambda m: export_csv(m, data_source_info=data_source_info),
            "yaml": export_yaml,
            "markdown": lambda m: export_markdown(m, data_source_info=data_source_info),
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
