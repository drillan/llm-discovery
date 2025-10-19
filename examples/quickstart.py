#!/usr/bin/env python3
"""Quickstart example for llm-discovery Python API."""

import asyncio

from llm_discovery import DiscoveryClient
from llm_discovery.models.config import Config


async def main():
    """Main function demonstrating basic usage."""
    # Load configuration from environment variables
    config = Config.from_env()
    client = DiscoveryClient(config)

    print("Fetching models from all providers...")

    # Fetch models from all providers
    provider_snapshots = await client.fetch_all_models()

    print(f"\nFound {len(provider_snapshots)} provider(s)\n")

    # Display all models
    for provider in provider_snapshots:
        print(f"=== {provider.provider_name.upper()} ===")
        print(f"Models: {len(provider.models)}")
        print(f"Status: {provider.fetch_status.value}")

        for model in provider.models[:5]:  # Show first 5 models
            print(f"  - {model.model_id}: {model.model_name}")

        if len(provider.models) > 5:
            print(f"  ... and {len(provider.models) - 5} more")

        print()


if __name__ == "__main__":
    asyncio.run(main())
