"""
Script to debug the API error handling.
"""
import sys
import traceback
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the app
from app.main import app, db

# Import test helpers
from tests.test_helper import debug_exception, print_route_info, print_mock_calls

client = TestClient(app)


def debug_get_survey_404():
    """
    Debug the 404 issue with get_survey endpoint.
    """
    print("\n=== Debugging get_survey 404 ===")

    # Print route info
    print_route_info(app, "/surveys/{survey_id}")

    try:
        # Create a direct mock that will definitely return None
        mock_get_survey = MagicMock(return_value=None)

        # Patch at the exact point where the function is used
        with patch('app.main.db.get_survey_by_id', mock_get_survey):
            # Make the request
            response = client.get("/surveys/nonexistent")

            # Print response details
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.json()}")

            # Print mock calls
            print_mock_calls(mock_get_survey)
    except Exception as e:
        print("\nException occurred during test:")
        debug_exception(e)


def debug_exception_handling():
    """
    Test if the app is catching and handling HTTPExceptions correctly.
    """
    print("\n=== Debugging Exception Handling ===")

    # Create a mock that raises an HTTPException
    from fastapi import HTTPException

    def raise_http_exception(*args, **kwargs):
        raise HTTPException(status_code=404, detail="Item not found")

    mock_get_survey = MagicMock(side_effect=raise_http_exception)

    try:
        with patch('app.main.db.get_survey_by_id', mock_get_survey):
            response = client.get("/surveys/nonexistent")
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.json()}")
    except Exception as e:
        print("\nException occurred during test:")
        debug_exception(e)


def main():
    print("Starting API debug tests...")
    debug_get_survey_404()
    debug_exception_handling()
    print("\nDebug tests completed.")


if __name__ == "__main__":
    main()
