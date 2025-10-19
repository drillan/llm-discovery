"""Main CLI application."""

from importlib.metadata import PackageNotFoundError, version

import typer
from rich.console import Console

from llm_discovery.cli.commands.export import export_command
from llm_discovery.cli.commands.list import list_command
from llm_discovery.cli.commands.update import update_command

app = typer.Typer(
    name="llm-discovery",
    help="LLM model discovery and tracking system",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        try:
            pkg_version = version("llm-discovery")
            console.print(f"llm-discovery, version {pkg_version}")
        except PackageNotFoundError:
            # Use stderr for error messages
            error_console = Console(stderr=True)
            error_console.print("[red]Error: Could not retrieve package version.[/red]")
            error_console.print("This may indicate an improper installation.")
            error_console.print("\nPlease try reinstalling llm-discovery:")
            error_console.print("  uv pip install --reinstall llm-discovery")
            raise typer.Exit(1)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """LLM model discovery and tracking system."""
    pass


# Register commands
app.command(name="update")(update_command)
app.command(name="list")(list_command)
app.command(name="export")(export_command)


if __name__ == "__main__":
    app()
