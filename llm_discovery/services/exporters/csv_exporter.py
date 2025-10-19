"""CSV exporter for spreadsheet analysis."""

import csv
import json
from io import StringIO

from llm_discovery.models import Model


def export_csv(models: list[Model]) -> str:
    """Export models to CSV format (spreadsheet optimized).

    Args:
        models: List of models to export

    Returns:
        CSV string

    Raises:
        ValueError: If models list is empty
    """
    if not models:
        raise ValueError("models cannot be empty")

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "provider",
            "model_id",
            "model_name",
            "source",
            "fetched_at",
            "metadata",
        ],
    )

    writer.writeheader()

    for model in models:
        writer.writerow(
            {
                "provider": model.provider_name,
                "model_id": model.model_id,
                "model_name": model.model_name,
                "source": model.source.value,
                "fetched_at": model.fetched_at.isoformat(),
                "metadata": json.dumps(model.metadata) if model.metadata else "",
            }
        )

    return output.getvalue()
