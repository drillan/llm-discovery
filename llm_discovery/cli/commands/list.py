"""List command for displaying models."""

import typer

from llm_discovery.cli.output import console, create_models_table, display_error
from llm_discovery.exceptions import CacheCorruptedError
from llm_discovery.models.config import Config
from llm_discovery.services.discovery import DiscoveryService


def list_command() -> None:
    """List available models from cache.

    Displays cached models from all providers in a table format.
    Run 'llm-discovery update' first to fetch and cache model data.
    """
    try:
        # Load configuration (API keys not required for reading cache)
        try:
            config = Config.from_env(require_api_keys=False)
        except ValueError as e:
            display_error("Configuration error", str(e))
            raise typer.Exit(1)

        service = DiscoveryService(config)

        # FR-001: Explicit data source selection (cache or prebuilt)
        # Determine which data source to use
        cache_file = config.llm_discovery_cache_dir / "models_cache.toml"
        has_cache = cache_file.exists()
        has_prebuilt = service.prebuilt_loader.is_available()

        used_prebuilt = False  # Track data source for info display

        if has_cache:
            # Load from cache
            console.print("[dim]Loading from cache...[/dim]")
            try:
                models = service.get_cached_models()
                console.print(f"[dim](Loaded from cache: {cache_file})[/dim]")
            except CacheCorruptedError as e:
                display_error(
                    "Cache file is corrupted.",
                    f"Error: {e}\n\n"
                    "Please run 'llm-discovery update' to refresh the cache.",
                )
                raise typer.Exit(1)
        elif has_prebuilt:
            # FR-001: Use prebuilt data when cache not available
            console.print("[dim]Loading from prebuilt data...[/dim]")
            models = service.prebuilt_loader.load_models()
            console.print("[dim](Using prebuilt data - run 'update' for latest)[/dim]")
            used_prebuilt = True
        else:
            # No data source available
            display_error(
                "No data available.",
                "Please configure API keys and run 'llm-discovery update' to fetch model data.",
            )
            raise typer.Exit(1)

        # Display results
        if models:
            table = create_models_table(models)
            console.print(table)
            console.print(f"\n[bold]Total models: {len(models)}[/bold]")

            # Display data source information (FR-040)
            try:
                # Get data source info based on source used
                if used_prebuilt:
                    # Display prebuilt metadata
                    metadata = service.prebuilt_loader.get_metadata()
                    console.print(
                        f"\n[dim]Data Source: PREBUILT[/dim]"
                    )
                    console.print(
                        f"[dim]Generated At: {metadata.generated_at.strftime('%Y-%m-%d %H:%M UTC')}[/dim]"
                    )
                    # Calculate age
                    from datetime import UTC, datetime
                    age_hours = (datetime.now(UTC) - metadata.generated_at).total_seconds() / 3600
                    console.print(
                        f"[dim]Age: {age_hours:.1f} hours[/dim]"
                    )

                    # Warning for old data (>24h) (FR-041)
                    if age_hours > 24:
                        if age_hours > 168:  # 7 days
                            console.print(
                                f"\n[red bold]⚠ Warning: Data is very old ({age_hours/24:.1f} days).[/red bold]"
                            )
                            console.print(
                                "[red]Consider running 'llm-discovery update' to refresh data.[/red]"
                            )
                        else:
                            console.print(
                                f"\n[yellow]⚠ Warning: Data is {age_hours:.1f} hours old.[/yellow]"
                            )
                            console.print(
                                "[yellow]Consider running 'llm-discovery update' for latest data.[/yellow]"
                            )
                else:
                    # Display cache metadata
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
