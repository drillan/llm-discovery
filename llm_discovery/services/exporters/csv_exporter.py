"""CSV exporter for spreadsheet analysis."""

import csv
import json
from io import StringIO

from llm_discovery.models import DataSourceInfo, Model


def export_csv(
    models: list[Model], *, data_source_info: DataSourceInfo | None = None
) -> str:
    """Export models to CSV format (spreadsheet optimized).

    Args:
        models: List of models to export
        data_source_info: Optional data source information

    Returns:
        CSV string

    Raises:
        ValueError: If models list is empty
    """
    if not models:
        raise ValueError("models cannot be empty")

    output = StringIO()

    # Add data_source column if info available (FR-043)
    fieldnames = [
        "provider",
        "model_id",
        "model_name",
        "source",
        "fetched_at",
        "metadata",
    ]

    if data_source_info:
        fieldnames.insert(0, "data_source")
        fieldnames.insert(1, "source_timestamp")

    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()

    for model in models:
        row = {
            "provider": model.provider_name,
            "model_id": model.model_id,
            "model_name": model.model_name,
            "source": model.source.value,
            "fetched_at": model.fetched_at.isoformat(),
            "metadata": json.dumps(model.metadata) if model.metadata else "",
        }

        # Add data source columns if available
        if data_source_info:
            row["data_source"] = data_source_info.source_type.value
            row["source_timestamp"] = data_source_info.timestamp.isoformat()

        writer.writerow(row)

    return output.getvalue()
