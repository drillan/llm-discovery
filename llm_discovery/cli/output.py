"""Output utilities for CLI."""

import sys

from rich.console import Console
from rich.table import Table

from llm_discovery.models import Model

console = Console()
error_console = Console(stderr=True, style="red")


def create_models_table(models: list[Model]) -> Table:
    """Create Rich table for model display.

    Args:
        models: List of models to display

    Returns:
        Rich Table object
    """
    table = Table(title="LLM Models")

    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Model ID", style="magenta")
    table.add_column("Model Name", style="green")
    table.add_column("Source", style="yellow")
    table.add_column("Fetched At", style="blue")

    for model in models:
        table.add_row(
            model.provider_name,
            model.model_id,
            model.model_name,
            model.source.value,
            model.fetched_at.strftime("%Y-%m-%d %H:%M"),
        )

    return table


def display_error(message: str, suggestion: str | None = None) -> None:
    """Display error message to stderr.

    Args:
        message: Error message
        suggestion: Optional suggestion for resolution
    """
    error_console.print(f"Error: {message}")
    if suggestion:
        error_console.print(f"\n{suggestion}")
