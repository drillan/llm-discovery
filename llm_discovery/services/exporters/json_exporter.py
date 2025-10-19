"""JSON exporter for CI/CD integration."""

import json
from datetime import datetime

from llm_discovery.models import Model


def export_json(models: list[Model], *, indent: int = 2) -> str:
    """Export models to JSON format (CI/CD optimized).

    Args:
        models: List of models to export
        indent: Indentation width (default: 2)

    Returns:
        JSON string

    Raises:
        ValueError: If models list is empty
    """
    if not models:
        raise ValueError("models cannot be empty")

    # Group models by provider
    providers_dict: dict[str, list[dict]] = {}
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

    # Create CI/CD-optimized structure
    output = {
        "metadata": {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_models": len(models),
            "providers": list(providers_dict.keys()),
        },
        "models": providers_dict,
    }

    return json.dumps(output, indent=indent, ensure_ascii=False)
