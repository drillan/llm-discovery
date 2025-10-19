"""Unit tests for PrebuiltDataLoader."""

from unittest.mock import MagicMock, patch

import pytest


class TestPrebuiltDataLoaderURLHandling:
    """Test URL accessibility and error handling."""

    @patch("urllib.request.urlopen")
    def test_url_not_accessible_raises_not_found_error(self, mock_urlopen):
        """Given URL returns HTTP 404, load_models raises PrebuiltDataNotFoundError."""
        from urllib.error import HTTPError

        from llm_discovery.exceptions import PrebuiltDataNotFoundError
        from llm_discovery.services.prebuilt_loader import PrebuiltDataLoader

        # Mock HTTP 404 error
        mock_urlopen.side_effect = HTTPError(
            url="https://example.com",
            code=404,
            msg="Not Found",
            hdrs=MagicMock(),
            fp=None,
        )

        loader = PrebuiltDataLoader()
        with pytest.raises(PrebuiltDataNotFoundError):
            loader.load_models()

    @patch("urllib.request.urlopen")
    def test_corrupted_json_raises_corrupted_error(self, mock_urlopen):
        """Given invalid JSON, load_models raises PrebuiltDataCorruptedError."""
        from llm_discovery.exceptions import PrebuiltDataCorruptedError
        from llm_discovery.services.prebuilt_loader import PrebuiltDataLoader

        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.read.return_value = b"{ invalid json"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        loader = PrebuiltDataLoader()
        with pytest.raises(PrebuiltDataCorruptedError):
            loader.load_models()

    @patch("urllib.request.urlopen")
    def test_validation_error_raises_validation_error(self, mock_urlopen):
        """Given JSON with invalid schema, load_models raises PrebuiltDataValidationError."""
        from llm_discovery.exceptions import PrebuiltDataValidationError
        from llm_discovery.services.prebuilt_loader import PrebuiltDataLoader

        # Mock response with invalid schema (missing required fields)
        invalid_data = b'{"invalid": "schema"}'
        mock_response = MagicMock()
        mock_response.read.return_value = invalid_data
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        loader = PrebuiltDataLoader()
        with pytest.raises(PrebuiltDataValidationError):
            loader.load_models()
