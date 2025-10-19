"""Contract tests for PrebuiltDataLoader.

These tests verify that PrebuiltDataLoader adheres to its public interface contract.
"""

import pytest


class TestPrebuiltDataLoaderContract:
    """Contract tests for PrebuiltDataLoader."""

    def test_is_available_returns_bool(self):
        """Contract: is_available() must return a boolean."""
        from llm_discovery.services.prebuilt_loader import PrebuiltDataLoader

        loader = PrebuiltDataLoader()
        result = loader.is_available()
        assert isinstance(result, bool)

    def test_load_models_returns_list(self):
        """Contract: load_models() must return a list of Model objects."""
        from llm_discovery.models import Model
        from llm_discovery.services.prebuilt_loader import PrebuiltDataLoader

        loader = PrebuiltDataLoader()

        # Skip if prebuilt data not available
        if not loader.is_available():
            pytest.skip("Prebuilt data not accessible")

        models = loader.load_models()
        assert isinstance(models, list)
        if models:  # If not empty, verify Model type
            assert all(isinstance(m, Model) for m in models)

    def test_get_metadata_returns_metadata_object(self):
        """Contract: get_metadata() must return PrebuiltDataMetadata object."""
        from llm_discovery.models import PrebuiltDataMetadata
        from llm_discovery.services.prebuilt_loader import PrebuiltDataLoader

        loader = PrebuiltDataLoader()

        # Skip if prebuilt data not available
        if not loader.is_available():
            pytest.skip("Prebuilt data not accessible")

        metadata = loader.get_metadata()
        assert isinstance(metadata, PrebuiltDataMetadata)

    def test_get_age_hours_returns_float(self):
        """Contract: get_age_hours() must return a float."""
        from llm_discovery.services.prebuilt_loader import PrebuiltDataLoader

        loader = PrebuiltDataLoader()

        # Skip if prebuilt data not available
        if not loader.is_available():
            pytest.skip("Prebuilt data not accessible")

        age = loader.get_age_hours()
        assert isinstance(age, float)
        assert age >= 0  # Age cannot be negative
