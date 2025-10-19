"""Update command for fetching and caching models."""

import asyncio
import json
from datetime import UTC, datetime

import typer

from llm_discovery.cli.output import console, display_error
from llm_discovery.exceptions import (
    AuthenticationError,
    PartialFetchError,
    ProviderFetchError,
)
from llm_discovery.models import ChangeType
from llm_discovery.models.config import Config
from llm_discovery.services.changelog_generator import ChangelogGenerator
from llm_discovery.services.discovery import DiscoveryService


def update_command(
    detect_changes: bool = typer.Option(
        False,
        "--detect-changes",
        help="Detect changes from previous snapshot",
    ),
) -> None:
    """Update local cache by fetching models from all providers.

    Fetches models from OpenAI, Google, and Anthropic providers and caches them locally.
    Displays a summary of fetched models by provider.
    """
    try:
        # Load configuration
        try:
            config = Config.from_env()
        except ValueError as e:
            # Error message from Config.from_env() is already detailed
            display_error("Configuration Error", str(e))
            raise typer.Exit(1)

        service = DiscoveryService(config)

        # Fetch from APIs
        try:
            console.print("[dim]Fetching models from APIs...[/dim]")
            providers = asyncio.run(service.fetch_all_models())

            # Save to cache
            service.save_to_cache(providers)

            # Build summary output (FR-024 compliant)
            provider_counts = []
            total_models = 0

            for provider in providers:
                count = len(provider.models)
                total_models += count
                # Capitalize provider name for display
                display_name = provider.provider_name.capitalize()
                provider_counts.append(f"{display_name}: {count}")

            # Handle change detection
            if detect_changes:
                # Get list of snapshots
                snapshots = service.snapshot_service.list_snapshots()

                if len(snapshots) < 1:
                    # No previous snapshot - save current as baseline
                    snapshot_id = service.snapshot_service.save_snapshot(providers)
                    console.print(
                        "[yellow]No previous snapshot found. Saving current state as baseline.[/yellow]"
                    )
                    console.print(
                        "Next run with --detect-changes will detect changes from this baseline.\n"
                    )
                    console.print(f"[dim]Snapshot ID: {snapshot_id}[/dim]")
                else:
                    # Load previous snapshot and detect changes
                    previous_snapshot_id, _ = snapshots[0]
                    previous_snapshot = service.snapshot_service.load_snapshot(
                        previous_snapshot_id
                    )

                    # Create current snapshot
                    from llm_discovery.models import Snapshot

                    current_snapshot = Snapshot(providers=providers)

                    # Detect changes
                    changes = service.change_detector.detect_changes(
                        previous_snapshot, current_snapshot
                    )

                    if changes:
                        console.print("[bold green]Changes detected![/bold green]\n")

                        # Group changes by type
                        added = [c for c in changes if c.change_type == ChangeType.ADDED]
                        removed = [
                            c for c in changes if c.change_type == ChangeType.REMOVED
                        ]

                        if added:
                            console.print(f"[green]Added models ({len(added)}):[/green]")
                            for change in added:
                                console.print(f"  {change.model_id}")

                        if removed:
                            console.print(
                                f"\n[red]Removed models ({len(removed)}):[/red]"
                            )
                            for change in removed:
                                console.print(f"  {change.model_id}")

                        # Save changes.json
                        changes_file = config.llm_discovery_cache_dir / "changes.json"
                        changes_data = {
                            "previous_snapshot_id": str(previous_snapshot.snapshot_id),
                            "current_snapshot_id": str(current_snapshot.snapshot_id),
                            "detected_at": datetime.now(UTC).isoformat(),
                            "changes": [
                                {
                                    "type": c.change_type.value,
                                    "model_id": c.model_id,
                                    "model_name": c.model_name,
                                    "provider_name": c.provider_name,
                                }
                                for c in changes
                            ],
                        }
                        changes_file.write_text(
                            json.dumps(changes_data, indent=2), encoding="utf-8"
                        )

                        # Update CHANGELOG.md
                        changelog_file = config.llm_discovery_cache_dir / "CHANGELOG.md"
                        changelog_gen = ChangelogGenerator(changelog_file)
                        changelog_gen.append_to_changelog(changes, datetime.now(UTC))

                        console.print("\n[dim]Details saved to:[/dim]")
                        console.print(f"[dim]  - {changes_file}[/dim]")
                        console.print(f"[dim]  - {changelog_file}[/dim]")

                        # Save new snapshot
                        service.snapshot_service.save_snapshot(providers)
                    else:
                        console.print("[dim]No changes detected.[/dim]")

                    # Cleanup old snapshots
                    deleted = service.snapshot_service.cleanup_old_snapshots()
                    if deleted > 0:
                        console.print(f"\n[dim]Cleaned up {deleted} old snapshot(s)[/dim]")

            # Display summary (FR-024 compliant)
            # Format: "OpenAI: 15, Google: 20, Anthropic: 7 / Total: 42 / Cached to: ..."
            summary = ", ".join(provider_counts)
            cache_path = config.llm_discovery_cache_dir / "models_cache.toml"

            console.print(
                f"\n{summary} / Total: {total_models} / Cached to: {cache_path}"
            )

        except PartialFetchError as e:
            display_error(
                "Partial failure during model fetch.",
                f"Successful providers: {', '.join(e.successful_providers)}\n"
                f"Failed providers: {', '.join(e.failed_providers)}\n\n"
                "To ensure data consistency, processing has been aborted.\n"
                "Please resolve the issue with the failed provider and retry.",
            )
            raise typer.Exit(1)

        except ProviderFetchError as e:
            display_error(
                f"Failed to fetch models from {e.provider_name} API.",
                f"Cause: {e.cause}\n\n"
                "Suggested actions:\n"
                "  1. Check your internet connection\n"
                "  2. Verify API keys are set correctly\n"
                "  3. Check provider status pages\n"
                "  4. Retry the command later",
            )
            raise typer.Exit(1)

        except AuthenticationError as e:
            display_error(
                f"Authentication failed for {e.provider_name}.",
                f"Details: {e.details}\n\n"
                "Please check your API keys and credentials.",
            )
            raise typer.Exit(2)

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit code
        raise
    except ValueError as e:
        display_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
