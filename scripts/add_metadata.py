#!/usr/bin/env python3
"""Add metadata to prebuilt model data JSON.

This script takes a JSON file containing provider snapshots and adds
metadata (generated_at, generator, version) to create a complete
PrebuiltModelData file.

Usage:
    python scripts/add_metadata.py input.json output.json
"""

import json
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from llm_discovery.models import PrebuiltDataMetadata, PrebuiltModelData


def get_package_version() -> str:
    """Get llm-discovery package version.

    Returns:
        Package version string (e.g., "0.1.0")
    """
    try:
        return version("llm-discovery")
    except PackageNotFoundError:
        # Development mode - use placeholder
        return "0.0.0-dev"


def generate_metadata() -> PrebuiltDataMetadata:
    """Generate metadata for prebuilt data.

    Returns:
        PrebuiltDataMetadata object with current timestamp and version
    """
    return PrebuiltDataMetadata(
        generated_at=datetime.now(UTC),
        generator="llm-discovery",
        version=get_package_version(),
    )


def load_and_validate_input(input_path: Path) -> dict[str, list[Any]]:
    """Load and validate input JSON file.

    Args:
        input_path: Path to input JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If input file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ValueError: If data structure is invalid
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        with input_path.open() as f:
            data: dict[str, list[Any]] = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in input file: {e}", e.doc, e.pos
        ) from e

    # Validate that 'providers' key exists
    if "providers" not in data:
        msg = "Input JSON must contain 'providers' key"
        raise ValueError(msg)

    if not isinstance(data["providers"], list):
        msg = "'providers' must be a list"
        raise ValueError(msg)

    return data


def write_output(output_path: Path, data: PrebuiltModelData) -> None:
    """Write PrebuiltModelData to output JSON file.

    Args:
        output_path: Path to output JSON file
        data: PrebuiltModelData object to write
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON (minified for production)
    with output_path.open("w") as f:
        json.dump(data.model_dump(mode="json"), f, separators=(",", ":"))


def main() -> int:
    """Main entry point for metadata addition script.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python scripts/add_metadata.py <input.json> <output.json>")
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    try:
        # Load and validate input
        input_data = load_and_validate_input(input_path)

        # Generate metadata
        metadata = generate_metadata()

        # Create PrebuiltModelData with metadata
        prebuilt_data = PrebuiltModelData(
            metadata=metadata, providers=input_data["providers"]
        )

        # Validate complete data structure
        # (pydantic validation happens in PrebuiltModelData constructor)

        # Write output
        write_output(output_path, prebuilt_data)

        print(f"✓ Metadata added successfully: {output_path}")
        return 0

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        error_type = type(e).__name__
        print(f"✗ {error_type}: {e}", file=sys.stderr)
        return 1
    except ValidationError as e:
        print("✗ Data validation error:", file=sys.stderr)
        for error in e.errors():
            print(f"  - {error['loc']}: {error['msg']}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
