import pytest
from app.db import MockRPCDatabase, simulate_rpc_call
import uuid
from unittest.mock import patch, MagicMock


def test_get_all_surveys():
    """Test retrieving all surveys."""
    db = MockRPCDatabase()
    surveys = db.get_all_surveys()
    assert len(surveys) > 0
    assert surveys[0]["name"] == "Ice Cream Preference"


def test_get_survey_by_id():
    """Test retrieving a survey by ID."""
    db = MockRPCDatabase()
    survey = db.get_survey_by_id("1")
    assert survey is not None
    assert survey["name"] == "Ice Cream Preference"


def test_get_nonexistent_survey():
    """Test retrieving a nonexistent survey."""
    db = MockRPCDatabase()
    survey = db.get_survey_by_id("999")
    assert survey is None


def test_create_conversation():
    """Test creating a new conversation."""
    db = MockRPCDatabase()
    conversation_id = db.create_conversation("1", "1")
    assert isinstance(conversation_id, str)

    # Verify the conversation was created
    conversation = db.get_conversation_state(conversation_id)
    assert conversation is not None
    assert conversation["customer_id"] == "1"
    assert conversation["survey_id"] == "1"
    assert conversation["status"] == "active"


def test_add_message_to_conversation():
    """Test adding a message to a conversation."""
    db = MockRPCDatabase()
    conversation_id = db.create_conversation("1", "1")

    # Add a message
    success = db.add_message_to_conversation(
        conversation_id, "BOT", "Test message")
    assert success is True

    # Verify the message was added
    messages = db.get_conversation_messages(conversation_id)
    assert len(messages) == 1
    assert messages[0]["sender"] == "BOT"
    assert messages[0]["content"] == "Test message"


@patch('app.db.random.random')
def test_simulate_rpc_call_success(mock_random):
    """Test successful RPC call simulation."""
    mock_random.return_value = 0.5  # Higher than 0.1, so no error
    try:
        simulate_rpc_call()
        # If we reach here, no exception was raised
        assert True
    except ConnectionError:
        # Should not reach here
        assert False


@patch('app.db.random.random')
def test_simulate_rpc_call_failure(mock_random):
    """Test RPC call failure simulation."""
    mock_random.return_value = 0.05  # Lower than 0.1, so error is raised
    with pytest.raises(ConnectionError):
        simulate_rpc_call()
