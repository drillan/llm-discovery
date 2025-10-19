"""JSON exporter for CI/CD integration."""

import json
from datetime import UTC, datetime
from typing import Any

from llm_discovery.models import DataSourceInfo, Model


def export_json(
    models: list[Model],
    *,
    indent: int = 2,
    data_source_info: DataSourceInfo | None = None,
) -> str:
    """Export models to JSON format (CI/CD optimized).

    Args:
        models: List of models to export
        indent: Indentation width (default: 2)
        data_source_info: Optional data source information

    Returns:
        JSON string

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

    # Create CI/CD-optimized structure with data source info
    metadata: dict[str, Any] = {
        "version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_models": len(models),
        "providers": list(providers_dict.keys()),
    }

    # Add data source information if available (FR-042)
    if data_source_info:
        metadata["data_source"] = data_source_info.source_type.value
        metadata["source_timestamp"] = data_source_info.timestamp.isoformat()
        metadata["data_age_hours"] = round(data_source_info.age_hours, 2)

    output = {
        "metadata": metadata,
        "models": providers_dict,
    }

    return json.dumps(output, indent=indent, ensure_ascii=False)
