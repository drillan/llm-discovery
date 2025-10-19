"""Markdown exporter for documentation."""

from llm_discovery.models import Model


def export_markdown(models: list[Model]) -> str:
    """Export models to Markdown format (documentation optimized).

    Args:
        models: List of models to export

    Returns:
        Markdown string

    Raises:
        ValueError: If models list is empty
    """
    if not models:
        raise ValueError("models cannot be empty")

    lines = [
        "# LLM Models",
        "",
        f"**Total Models**: {len(models)}",
        "",
    ]

    # Group by provider
    providers_dict: dict[str, list[Model]] = {}
    for model in models:
        if model.provider_name not in providers_dict:
            providers_dict[model.provider_name] = []
        providers_dict[model.provider_name].append(model)

    # Generate markdown for each provider
    for provider_name, provider_models in providers_dict.items():
        lines.append(f"## {provider_name.title()}")
        lines.append("")
        lines.append("| Model ID | Model Name | Source | Fetched At |")
        lines.append("|----------|------------|--------|------------|")

        for model in provider_models:
            lines.append(
                f"| {model.model_id} | {model.model_name} | "
                f"{model.source.value} | {model.fetched_at.strftime('%Y-%m-%d %H:%M')} |"
            )

        lines.append("")

    return "\n".join(lines)
