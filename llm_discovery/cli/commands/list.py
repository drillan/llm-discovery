"""List command for displaying models."""

import typer

from llm_discovery.cli.output import console, create_models_table, display_error
from llm_discovery.exceptions import (
    CacheCorruptedError,
    CacheNotFoundError,
)
from llm_discovery.models.config import Config
from llm_discovery.services.discovery import DiscoveryService


def list_command() -> None:
    """List available models from cache.

    Displays cached models from all providers in a table format.
    Run 'llm-discovery update' first to fetch and cache model data.
    """
    try:
        # Load configuration
        config = Config.from_env()
        service = DiscoveryService(config)

        # Load from cache (FR-025: Read-only operation)
        try:
            console.print("[dim]Loading from cache...[/dim]")
            models = service.get_cached_models()
            console.print(
                f"[dim](Loaded from cache: {config.llm_discovery_cache_dir / 'models_cache.toml'})[/dim]"
            )
        except CacheNotFoundError:
            # FR-025: Clear error message when cache doesn't exist
            display_error(
                "No cached data available.",
                "Please run 'llm-discovery update' first to fetch model data.",
            )
            raise typer.Exit(1)
        except CacheCorruptedError as e:
            # Cache is corrupted - show error
            display_error(
                "Cache file is corrupted.",
                f"Error: {e}\n\n"
                "Please run 'llm-discovery update' to refresh the cache.",
            )
            raise typer.Exit(1)

        # Display results
        if models:
            table = create_models_table(models)
            console.print(table)
            console.print(f"\n[bold]Total models: {len(models)}[/bold]")

            # Display data source information (FR-040)
            try:
                data_source_info = service.get_data_source_info()
                if data_source_info:
                    console.print(
                        f"\n[dim]Data Source: {data_source_info.source_type.value.upper()}[/dim]"
                    )
                    console.print(
                        f"[dim]Last Updated: {data_source_info.timestamp.strftime('%Y-%m-%d %H:%M UTC')}[/dim]"
                    )
                    console.print(
                        f"[dim]Age: {data_source_info.age_hours:.1f} hours[/dim]"
                    )

                    # Warning for old data (>24h) (FR-041)
                    if data_source_info.age_hours > 24:
                        if data_source_info.age_hours > 168:  # 7 days
                            console.print(
                                f"\n[red bold]⚠ Warning: Data is very old ({data_source_info.age_hours/24:.1f} days).[/red bold]"
                            )
                            console.print(
                                "[red]Consider running 'llm-discovery update' to refresh data.[/red]"
                            )
                        else:
                            console.print(
                                f"\n[yellow]⚠ Warning: Data is {data_source_info.age_hours:.1f} hours old.[/yellow]"
                            )
                            console.print(
                                "[yellow]Consider running 'llm-discovery update' for fresher data.[/yellow]"
                            )
            except Exception:
                # Gracefully degrade if data source info not available
                pass
        else:
            console.print("[yellow]No models found.[/yellow]")

    except ValueError as e:
        display_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
