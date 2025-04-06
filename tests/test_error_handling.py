import pytest
from unittest.mock import patch, MagicMock, call
from app.main import with_retry


class TestErrorHandling:
    def test_with_retry_success_first_try(self):
        """Test successful function call on first try."""
        mock_func = MagicMock()
        mock_func.return_value = "success"

        result = with_retry(mock_func, "arg1", "arg2", kwarg1="value1")

        assert result == "success"
        mock_func.assert_called_once_with("arg1", "arg2", kwarg1="value1")

    def test_with_retry_success_after_retries(self):
        """Test successful function call after retries."""
        mock_func = MagicMock()
        # Fail twice, then succeed
        mock_func.side_effect = [
            ConnectionError("First failure"),
            ConnectionError("Second failure"),
            "success"
        ]

        result = with_retry(mock_func, "arg", max_retries=3)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_with_retry_all_failures(self):
        """Test function call failing all retries."""
        mock_func = MagicMock()
        mock_func.side_effect = ConnectionError("Failure")

        with pytest.raises(ConnectionError):
            with_retry(mock_func, "arg", max_retries=3)

        assert mock_func.call_count == 3

    def test_with_retry_non_connection_error(self):
        """Test function call with non-ConnectionError exception."""
        mock_func = MagicMock()
        mock_func.side_effect = ValueError("Non-connection error")

        with pytest.raises(ValueError):
            with_retry(mock_func, "arg")

        mock_func.assert_called_once()
