import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import json
from datetime import datetime, timedelta

# Import the app but patch the db
from app.main import app
from app.db import MockRPCDatabase

# Setup test client


@pytest.fixture
def client():
    return TestClient(app)

# Mock database for testing


@pytest.fixture
def mock_db():
    # Create a mock database instance
    db_mock = MagicMock(spec=MockRPCDatabase)

    # Setup default test data
    test_customer = {"id": "1", "name": "Test User",
                     "email": "test@example.com"}
    test_survey = {
        "id": "test_survey",
        "name": "Test Survey",
        "questions": [
            {
                "id": "q1",
                "text": "Test Question 1",
                "options": [
                    {"id": "1", "text": "Option 1"},
                    {"id": "2", "text": "Option 2"}
                ]
            },
            {
                "id": "q2",
                "text": "Would you like to provide feedback?",
                "options": []  # Open question
            }
        ]
    }
    test_conversation = {
        "id": "test_conv",
        "customer_id": "1",
        "survey_id": "test_survey",
        "current_question_index": 0,
        "answers": {},
        "messages": [],
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # Configure method returns
    db_mock.get_customer_info.return_value = test_customer
    db_mock.get_survey_by_id.return_value = test_survey
    db_mock.get_all_surveys.return_value = [test_survey]
    db_mock.get_conversation_state.return_value = test_conversation
    db_mock.create_conversation.return_value = "test_conv"
    db_mock.add_message_to_conversation.return_value = True
    db_mock.get_conversation_messages.return_value = []
    db_mock.resume_conversation.return_value = test_conversation
    db_mock.get_customer_active_surveys.return_value = [test_conversation]

    # Patch the database in main
    with patch('app.main.db', db_mock):
        yield db_mock

# Fixture for WebSocket testing


@pytest.fixture
def websocket_client():
    from fastapi.testclient import TestClient
    client = TestClient(app)
    return client
