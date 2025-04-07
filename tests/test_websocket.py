import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from app.main import app, manager, process_websocket_message


# Test WebSocket connection and basic functionality
def test_websocket_connection(websocket_client, mock_db):
    # Setup conversation in mock DB
    conversation = {
        "id": "ws_test",
        "customer_id": "1",
        "survey_id": "test_survey",
        "current_question_index": 0,
        "answers": {},
        "messages": [],
        "status": "active",
        "created_at": "2023-01-01T12:00:00",
        "updated_at": "2023-01-01T12:00:00"
    }
    mock_db.get_conversation_state.return_value = conversation

    # Setup customer and survey
    customer = {"id": "1", "name": "Test User", "email": "test@example.com"}
    survey = {
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
            }
        ]
    }
    mock_db.get_customer_info.return_value = customer
    mock_db.get_survey_by_id.return_value = survey
    mock_db.get_conversation_messages.return_value = []

    # Connect to WebSocket
    with websocket_client.websocket_connect("/ws/ws_test") as websocket:
        # Check initial state message
        response = json.loads(websocket.receive_text())
        assert response["type"] == "state"
        assert response["conversation"] == conversation
        assert response["customer"] == customer
        assert response["survey"] == survey

        # Check history message
        response = json.loads(websocket.receive_text())
        assert response["type"] == "history"
        assert response["messages"] == []

        # Send a message
        websocket.send_json({"content": "Test message"})

        # Instead of checking specific arguments, verify that the method was called at least once
        # This is because the WebSocket handler is processing the message and may make additional calls
        assert mock_db.add_message_to_conversation.called

        # Verify that at least one call included the USER as sender
        found_user_message = False
        for call in mock_db.add_message_to_conversation.call_args_list:
            args = call[0]
            if len(args) >= 3 and args[0] == "ws_test" and args[1] == "USER" and args[2] == "Test message":
                found_user_message = True
                break

        assert found_user_message, "No call found with the USER message"


# Test WebSocket error handling
def test_websocket_errors(websocket_client, mock_db):
    # Test conversation not found
    mock_db.get_conversation_state.return_value = None

    with websocket_client.websocket_connect("/ws/nonexistent") as websocket:
        response = json.loads(websocket.receive_text())
        assert response["type"] == "error"
        assert "not found" in response["message"]

    # Test customer not found
    mock_db.get_conversation_state.return_value = {
        "id": "test", "customer_id": "999", "survey_id": "test"}
    mock_db.get_customer_info.return_value = None

    with websocket_client.websocket_connect("/ws/test") as websocket:
        response = json.loads(websocket.receive_text())
        assert response["type"] == "error"
        assert "not found" in response["message"]

    # Test survey not found
    mock_db.get_conversation_state.return_value = {
        "id": "test", "customer_id": "1", "survey_id": "999"}
    mock_db.get_customer_info.return_value = {"id": "1", "name": "Test"}
    mock_db.get_survey_by_id.return_value = None

    with websocket_client.websocket_connect("/ws/test") as websocket:
        response = json.loads(websocket.receive_text())
        assert response["type"] == "error"
        assert "not found" in response["message"]

    # Test connection error - instead of expecting a disconnect, check for error message
    mock_db.get_conversation_state.side_effect = ConnectionError("Test error")

    with websocket_client.websocket_connect("/ws/test") as websocket:
        response = json.loads(websocket.receive_text())
        assert response["type"] == "error"
        assert "unavailable" in response["message"] or "error" in response["message"]


# Test WebSocket message processing
@pytest.mark.asyncio
async def test_process_websocket_message():
    # Create mock WebSocket, conversation, and database
    websocket = MagicMock()
    websocket.send_json = AsyncMock()

    conversation = {
        "id": "test_conv",
        "customer_id": "1",
        "survey_id": "test_survey",
        "current_question_index": 0,
        "answers": {},
        "status": "active"
    }

    customer = {"id": "1", "name": "Test User"}

    survey = {
        "id": "test_survey",
        "questions": [
            {
                "id": "q1",
                "text": "Question 1",
                "options": [
                    {"id": "1", "text": "Option 1"},
                    {"id": "2", "text": "Option 2"}
                ]
            },
            {
                "id": "q2",
                "text": "Would you like to provide feedback?",
                "options": []
            }
        ]
    }

    # Mock the with_retry function
    with patch('app.main.with_retry') as mock_with_retry:
        # Configure mock returns
        mock_with_retry.side_effect = lambda func, *args, **kwargs: {
            'get_customer_info': lambda customer_id: customer,
            'get_survey_by_id': lambda survey_id: survey,
            'save_conversation_state': lambda conv_id, conv: None,
            'add_message_to_conversation': lambda conv_id, sender, message: True
        }.get(func.__name__, lambda *a, **kw: None)(*args, **kwargs)

        # Test processing a message for the first question
        await process_websocket_message(websocket, "test_conv", "1", conversation)

        # Check that the answer was stored
        assert conversation["answers"]["q1"] == "1"

        # Check that current_question_index was incremented
        assert conversation["current_question_index"] == 1

        # Check that bot response was sent
        websocket.send_json.assert_called()
        args = websocket.send_json.call_args[0][0]
        assert args["type"] == "message"
        assert args["sender"] == "BOT"
        assert "Great choice!" in args["content"]

        # Reset the mock
        websocket.send_json.reset_mock()

        # Test processing a "yes" response to the feedback question
        # Set to the feedback question
        conversation["current_question_index"] = 1
        await process_websocket_message(websocket, "test_conv", "yes", conversation)

        # Check that awaiting_detailed_feedback was set
        assert conversation.get("awaiting_detailed_feedback") is True

        # Check that bot response was sent asking for feedback
        websocket.send_json.assert_called()
        args = websocket.send_json.call_args[0][0]
        assert args["type"] == "message"
        assert args["sender"] == "BOT"
        assert "Please share your thoughts" in args["content"]
