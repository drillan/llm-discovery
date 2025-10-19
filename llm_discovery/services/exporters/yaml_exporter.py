"""YAML exporter for configuration files."""

from typing import Any

import yaml

from llm_discovery.models import Model


def export_yaml(models: list[Model]) -> str:
    """Export models to YAML format (configuration file optimized).

    Args:
        models: List of models to export

    Returns:
        YAML string

    Raises:
        ValueError: If models list is empty
    """
    if not models:
        raise ValueError("models cannot be empty")

    # Group models by provider
    providers_dict: dict[str, list[dict[str, Any]]] = {}
    for model in models:
        if model.provider_name not in providers_dict:
            providers_dict[model.provider_name] = []

        providers_dict[model.provider_name].append(
            {
                "id": model.model_id,
                "name": model.model_name,
                "source": model.source.value,
                "fetched_at": model.fetched_at.isoformat(),
                "metadata": model.metadata,
            }
        )

    # Create YAML structure
    output = {
        "llm_models": {
            "providers": providers_dict,
            "total_count": len(models),
        }
    }

    return yaml.dump(output, default_flow_style=False, allow_unicode=True, sort_keys=False)
