"""Update command for fetching and caching models."""

import asyncio

import typer

from llm_discovery.cli.output import console, display_error
from llm_discovery.exceptions import (
    AuthenticationError,
    PartialFetchError,
    ProviderFetchError,
)
from llm_discovery.models.config import Config
from llm_discovery.services.discovery import DiscoveryService


def update_command() -> None:
    """Update local cache by fetching models from all providers.

    Fetches models from OpenAI, Google, and Anthropic providers and caches them locally.
    Displays a summary of fetched models by provider.
    """
    try:
        # Load configuration
        config = Config.from_env()
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

            # Format: "OpenAI: 15, Google: 20, Anthropic: 7 / Total: 42 / Cached to: ..."
            summary = ", ".join(provider_counts)
            cache_path = config.llm_discovery_cache_dir / "models_cache.toml"

            console.print(
                f"{summary} / Total: {total_models} / Cached to: {cache_path}"
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
