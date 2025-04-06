import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from unittest.mock import patch, MagicMock

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"healthy": True}


@patch('app.main.db.get_all_surveys')
def test_get_surveys(mock_get_all_surveys):
    """Test retrieving all surveys endpoint."""
    mock_get_all_surveys.return_value = [{"id": "1", "name": "Test Survey"}]
    response = client.get("/surveys")
    assert response.status_code == 200
    assert response.json() == [{"id": "1", "name": "Test Survey"}]


@patch('app.main.db.get_survey_by_id')
def test_get_survey(mock_get_survey_by_id):
    """Test retrieving a specific survey endpoint."""
    mock_get_survey_by_id.return_value = {"id": "1", "name": "Test Survey"}
    response = client.get("/surveys/1")
    assert response.status_code == 200
    assert response.json() == {"id": "1", "name": "Test Survey"}


@patch('app.main.db.get_survey_by_id')
def test_get_nonexistent_survey(mock_get_survey_by_id):
    """Test retrieving a nonexistent survey endpoint."""
    mock_get_survey_by_id.return_value = None
    response = client.get("/surveys/999")
    assert response.status_code == 404


@patch('app.main.db.create_conversation')
@patch('app.main.db.get_survey_by_id')
@patch('app.main.db.get_customer_info')
def test_start_conversation(mock_get_customer_info, mock_get_survey_by_id, mock_create_conversation):
    """Test starting a new conversation endpoint."""
    mock_get_customer_info.return_value = {"name": "John Doe"}
    mock_get_survey_by_id.return_value = {"id": "1", "name": "Test Survey"}
    mock_create_conversation.return_value = "test-conversation-id"

    response = client.post(
        "/conversations",
        json={"customer_id": "1", "survey_id": "1"}
    )

    assert response.status_code == 201
    assert response.json() == {"conversation_id": "test-conversation-id"}


@patch('app.main.db.get_conversation_state')
def test_get_nonexistent_conversation(mock_get_conversation_state):
    """Test retrieving a nonexistent conversation endpoint."""
    mock_get_conversation_state.return_value = None
    response = client.get("/conversations/nonexistent-id")
    assert response.status_code == 404


@patch('app.main.db.get_conversation_messages')
def test_get_messages(mock_get_conversation_messages):
    """Test retrieving conversation messages endpoint."""
    mock_messages = [
        {"sender": "BOT", "content": "Test message",
            "timestamp": "2023-01-01T00:00:00"}
    ]
    mock_get_conversation_messages.return_value = mock_messages

    response = client.get("/conversations/test-id/messages")
    assert response.status_code == 200
    assert response.json() == mock_messages


@patch('app.main.db.add_message_to_conversation')
@patch('app.main.db.get_conversation_state')
def test_send_message(mock_get_conversation_state, mock_add_message):
    """Test sending a message to a conversation endpoint."""
    mock_get_conversation_state.return_value = {
        "id": "test-id",
        "customer_id": "1",
        "survey_id": "1"
    }
    mock_add_message.return_value = True

    response = client.post(
        "/conversations/test-id/messages",
        json={"content": "Test message"}
    )

    assert response.status_code == 201
    assert response.json() == {"status": "message received"}
