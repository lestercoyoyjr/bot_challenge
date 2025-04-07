import pytest
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime
import time

from app.db import MockRPCDatabase, mock_db

# Test the database mock initialization


def test_mock_db_initialization():
    # Verify initial data structure
    assert "conversations" in mock_db
    assert "customers" in mock_db
    assert "surveys" in mock_db
    assert "survey_responses" in mock_db

    # Verify sample data
    assert len(mock_db["customers"]) > 0
    assert len(mock_db["surveys"]) > 0
    assert isinstance(mock_db["surveys"][0]["questions"], list)

# Test the RPC simulation


@patch('app.db.time.sleep')  # Patch sleep to speed up tests
def test_simulate_rpc_call(mock_sleep):
    from app.db import simulate_rpc_call

    # Mock random to always return 0.2 (below failure threshold)
    with patch('app.db.random.random', return_value=0.2):
        # Should not raise an exception
        simulate_rpc_call()
        mock_sleep.assert_called_once()

    # Reset mock
    mock_sleep.reset_mock()

    # Mock random to return 0.05 (below failure threshold)
    with patch('app.db.random.random', return_value=0.05):
        # Should raise ConnectionError
        with pytest.raises(ConnectionError):
            simulate_rpc_call()
        mock_sleep.assert_called_once()

# Test get_conversation_state method


@patch('app.db.simulate_rpc_call')
def test_get_conversation_state(mock_simulate):
    db = MockRPCDatabase()

    # Test with nonexistent conversation
    result = db.get_conversation_state("nonexistent")
    mock_simulate.assert_called_once()
    assert result is None

    # Test with existing conversation
    mock_simulate.reset_mock()
    mock_db["conversations"]["test_conv"] = {
        "id": "test_conv", "status": "active"}

    result = db.get_conversation_state("test_conv")
    mock_simulate.assert_called_once()
    assert result == {"id": "test_conv", "status": "active"}

# Test save_conversation_state method


@patch('app.db.simulate_rpc_call')
def test_save_conversation_state(mock_simulate):
    db = MockRPCDatabase()
    test_state = {"id": "new_conv", "status": "active"}

    # Save a new conversation
    db.save_conversation_state("new_conv", test_state)
    mock_simulate.assert_called_once()
    assert mock_db["conversations"]["new_conv"] == test_state

    # Update an existing conversation
    mock_simulate.reset_mock()
    updated_state = {"id": "new_conv", "status": "completed"}
    db.save_conversation_state("new_conv", updated_state)
    mock_simulate.assert_called_once()
    assert mock_db["conversations"]["new_conv"] == updated_state

# Test get_customer_info method


@patch('app.db.simulate_rpc_call')
def test_get_customer_info(mock_simulate):
    db = MockRPCDatabase()

    # Test with existing customer
    result = db.get_customer_info("1")
    mock_simulate.assert_called_once()
    assert result == mock_db["customers"]["1"]

    # Test with nonexistent customer
    mock_simulate.reset_mock()
    result = db.get_customer_info("nonexistent")
    mock_simulate.assert_called_once()
    assert result is None

# Test save_survey_response method


@patch('app.db.simulate_rpc_call')
def test_save_survey_response(mock_simulate):
    db = MockRPCDatabase()
    initial_count = len(mock_db["survey_responses"])

    # Save a new response
    test_response = {"conversation_id": "test_conv", "answers": {"q1": "1"}}
    db.save_survey_response(test_response)
    mock_simulate.assert_called_once()

    # Verify the response was added
    assert len(mock_db["survey_responses"]) == initial_count + 1
    assert mock_db["survey_responses"][-1] == test_response

# Test get_all_surveys and get_survey_by_id methods


@patch('app.db.simulate_rpc_call')
def test_survey_methods(mock_simulate):
    db = MockRPCDatabase()

    # Test get_all_surveys
    all_surveys = db.get_all_surveys()
    mock_simulate.assert_called_once()
    assert all_surveys == mock_db["surveys"]

    # Test get_survey_by_id with existing survey
    mock_simulate.reset_mock()
    survey = db.get_survey_by_id("1")
    mock_simulate.assert_called_once()
    assert survey == mock_db["surveys"][0]

    # Test get_survey_by_id with nonexistent survey
    mock_simulate.reset_mock()
    survey = db.get_survey_by_id("nonexistent")
    mock_simulate.assert_called_once()
    assert survey is None

# Test create_conversation method


@patch('app.db.simulate_rpc_call')
@patch('app.db.uuid.uuid4')
def test_create_conversation(mock_uuid, mock_simulate):
    db = MockRPCDatabase()
    test_uuid = "test-uuid-12345"
    mock_uuid.return_value = test_uuid

    # Test with valid customer and survey
    conv_id = db.create_conversation("1", "1")
    mock_simulate.assert_called_once()
    assert conv_id == str(test_uuid)

    # Verify the conversation was created
    assert str(test_uuid) in mock_db["conversations"]
    assert mock_db["conversations"][str(test_uuid)]["customer_id"] == "1"
    assert mock_db["conversations"][str(test_uuid)]["survey_id"] == "1"

    # Test with invalid customer or survey
    mock_simulate.reset_mock()
    with pytest.raises(ValueError):
        db.create_conversation("999", "1")  # Invalid customer

    mock_simulate.reset_mock()
    with pytest.raises(ValueError):
        db.create_conversation("1", "999")  # Invalid survey

# Test conversation message methods


@patch('app.db.simulate_rpc_call')
def test_conversation_messages(mock_simulate):
    db = MockRPCDatabase()

    # Setup a test conversation
    test_conv = {
        "id": "message_test",
        "messages": [
            {"sender": "BOT", "content": "Hello!",
                "timestamp": datetime.now().isoformat()}
        ]
    }
    mock_db["conversations"]["message_test"] = test_conv

    # Test get_conversation_messages
    messages = db.get_conversation_messages("message_test")
    mock_simulate.assert_called_once()
    assert messages == test_conv["messages"]

    # Test get_conversation_messages for nonexistent conversation
    mock_simulate.reset_mock()
    messages = db.get_conversation_messages("nonexistent")
    mock_simulate.assert_called_once()
    assert messages == []

    # Test add_message_to_conversation
    mock_simulate.reset_mock()
    result = db.add_message_to_conversation(
        "message_test", "USER", "Hello back!")
    mock_simulate.assert_called_once()
    assert result is True
    assert len(mock_db["conversations"]["message_test"]["messages"]) == 2
    assert mock_db["conversations"]["message_test"]["messages"][1]["sender"] == "USER"
    assert mock_db["conversations"]["message_test"]["messages"][1]["content"] == "Hello back!"

    # Test add_message_to_conversation for nonexistent conversation
    mock_simulate.reset_mock()
    result = db.add_message_to_conversation("nonexistent", "USER", "Hello")
    mock_simulate.assert_called_once()
    assert result is False

# Test customer surveys methods


@patch('app.db.simulate_rpc_call')
def test_customer_surveys_methods(mock_simulate):
    db = MockRPCDatabase()

    # Setup test conversations for a customer
    mock_db["conversations"] = {
        "active1": {"id": "active1", "customer_id": "1", "status": "active"},
        "active2": {"id": "active2", "customer_id": "1", "status": "active"},
        "completed": {"id": "completed", "customer_id": "1", "status": "completed"},
        "other_customer": {"id": "other", "customer_id": "2", "status": "active"}
    }

    # Test get_customer_active_surveys
    active_surveys = db.get_customer_active_surveys("1")
    mock_simulate.assert_called_once()
    assert len(active_surveys) == 2
    assert all(s["status"] == "active" for s in active_surveys)
    assert all(s["customer_id"] == "1" for s in active_surveys)

    # Test resume_conversation
    mock_simulate.reset_mock()
    # Create a test conversation to resume
    test_conv = {
        "id": "resume_test",
        "customer_id": "1",
        "survey_id": "1",
        "status": "active",
        "current_question_index": 1,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    mock_db["conversations"]["resume_test"] = test_conv

    # Test successful resume
    resumed_conv = db.resume_conversation("resume_test")
    mock_simulate.assert_called_once()
    assert resumed_conv is not None
    assert "resumed_at" in resumed_conv

    # Test resuming a completed conversation
    mock_simulate.reset_mock()
    mock_db["conversations"]["completed_test"] = {
        "id": "completed_test",
        "status": "completed"
    }
    resumed_conv = db.resume_conversation("completed_test")
    mock_simulate.assert_called_once()
    assert resumed_conv is None

    # Test resuming a nonexistent conversation
    mock_simulate.reset_mock()
    resumed_conv = db.resume_conversation("nonexistent")
    mock_simulate.assert_called_once()
    assert resumed_conv is None
