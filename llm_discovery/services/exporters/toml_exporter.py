"""TOML exporter for interoperability."""

import tomli_w

from llm_discovery.models import Model


def export_toml(models: list[Model]) -> str:
    """Export models to TOML format (interoperability optimized).

    Args:
        models: List of models to export

    Returns:
        TOML string

    Raises:
        ValueError: If models list is empty
    """
    if not models:
        raise ValueError("models cannot be empty")

    # Group models by provider
    providers_list = []
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

    # Convert to TOML structure
    for provider_name, provider_models in providers_dict.items():
        providers_list.append(
            {
                "name": provider_name,
                "models": provider_models,
            }
        )

    output = {
        "llm_models": {
            "total_count": len(models),
        },
        "providers": providers_list,
    }

    return tomli_w.dumps(output)
