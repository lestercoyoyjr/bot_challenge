import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


class TestConversationFlow:
    @patch('app.main.db.get_customer_info')
    @patch('app.main.db.get_survey_by_id')
    @patch('app.main.db.create_conversation')
    def test_complete_survey_flow(self, mock_create_conv, mock_get_survey, mock_get_customer):
        # Mock customer
        mock_get_customer.return_value = {"name": "John Doe"}

        # Mock survey
        mock_get_survey.return_value = {
            "id": "1",
            "name": "Ice Cream Preference",
            "questions": [
                {
                    "id": "q1",
                    "text": "Which flavor of ice cream do you prefer?",
                    "options": [
                        {"id": "1", "text": "Vanilla"},
                        {"id": "2", "text": "Chocolate"},
                        {"id": "3", "text": "Strawberry"}
                    ]
                },
                {
                    "id": "q2",
                    "text": "Would you like to provide feedback?",
                    "options": []
                }
            ]
        }

        # Mock conversation creation
        mock_create_conv.return_value = "test-conv-id"

        # Start conversation
        response = client.post(
            "/conversations",
            json={"customer_id": "1", "survey_id": "1"}
        )
        assert response.status_code == 201
        conv_id = response.json()["conversation_id"]

        # Send flavor choice
        with patch('app.main.db.add_message_to_conversation', return_value=True):
            with patch('app.main.db.get_conversation_state', return_value={
                "id": conv_id,
                "customer_id": "1",
                "survey_id": "1",
                "current_question_index": 0,
                "answers": {},
                "messages": [],
                "status": "active",
            }):
                response = client.post(
                    f"/conversations/{conv_id}/messages",
                    json={"content": "2"}
                )
                assert response.status_code == 201

        # Send "Yes" response to feedback question
        with patch('app.main.db.add_message_to_conversation', return_value=True):
            with patch('app.main.db.get_conversation_state', return_value={
                "id": conv_id,
                "customer_id": "1",
                "survey_id": "1",
                "current_question_index": 1,
                "answers": {"q1": "2"},
                "messages": [],
                "status": "active",
            }):
                response = client.post(
                    f"/conversations/{conv_id}/messages",
                    json={"content": "Yes please"}
                )
                assert response.status_code == 201
