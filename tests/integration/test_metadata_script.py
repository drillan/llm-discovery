"""Integration tests for metadata addition script."""

import json
import subprocess
from pathlib import Path


class TestMetadataScript:
    """Test metadata addition script integration."""

    def test_metadata_script_adds_correct_metadata(self, tmp_path: Path):
        """Given valid provider snapshots JSON, script adds correct metadata."""
        # Create test input JSON
        input_data = {
            "providers": [
                {
                    "provider_name": "openai",
                    "fetched_at": "2025-10-19T00:00:00Z",
                    "fetch_status": "success",
                    "error_message": None,
                    "models": [
                        {
                            "model_id": "gpt-4",
                            "model_name": "GPT-4",
                            "provider_name": "openai",
                            "source": "api",
                            "fetched_at": "2025-10-19T00:00:00Z",
                            "metadata": {"created": 1234567890, "owned_by": "openai"},
                        }
                    ],
                }
            ]
        }

        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"

        input_file.write_text(json.dumps(input_data))

        # Run script
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "scripts/add_metadata.py",
                str(input_file),
                str(output_file),
            ],
            check=False, capture_output=True,
            text=True,
            timeout=10,
        )

        # Verify script succeeded
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Verify output file exists
        assert output_file.exists()

        # Verify output JSON
        output_data = json.loads(output_file.read_text())

        # Check metadata exists
        assert "metadata" in output_data
        assert "providers" in output_data

        # Check metadata fields
        metadata = output_data["metadata"]
        assert "generated_at" in metadata
        assert "generator" in metadata
        assert metadata["generator"] == "llm-discovery"
        assert "version" in metadata

        # Check providers preserved
        assert len(output_data["providers"]) == 1
        assert output_data["providers"][0]["provider_name"] == "openai"
