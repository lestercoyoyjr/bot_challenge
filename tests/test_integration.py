import pytest
from unittest.mock import patch, MagicMock
from app.main import process_user_response, with_retry
from datetime import datetime


class TestConversationFlow:
    @patch('app.main.db.get_conversation_state')
    @patch('app.main.db.get_customer_info')
    @patch('app.main.db.get_survey_by_id')
    @patch('app.main.db.save_conversation_state')
    @patch('app.main.db.add_message_to_conversation')
    def test_flavor_choice_response(self, mock_add_message, mock_save_state, mock_get_survey,
                                    mock_get_customer, mock_get_conversation):
        """Test processing a flavor choice response."""
        # Setup mock returns
        mock_get_conversation.return_value = {
            "id": "test-id",
            "customer_id": "1",
            "survey_id": "1",
            "current_question_index": 0,
            "answers": {},
            "messages": [],
            "status": "active"
        }

        mock_get_customer.return_value = {"name": "John Doe"}

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

        mock_add_message.return_value = True
        mock_save_state.return_value = None

        # Call the function
        process_user_response(
            "test-id", "2", mock_get_conversation.return_value)

        # Verify state was updated
        assert mock_save_state.called
        call_args = mock_save_state.call_args[0]
        assert call_args[0] == "test-id"
        assert call_args[1]["current_question_index"] == 1
        assert call_args[1]["answers"]["q1"] == "2"

        # Verify acknowledgment message was sent
        assert mock_add_message.called
        message_args = mock_add_message.call_args[0]
        assert "Chocolate" in message_args[2]  # Check message content

    @patch('app.main.db.get_conversation_state')
    @patch('app.main.db.get_customer_info')
    @patch('app.main.db.get_survey_by_id')
    @patch('app.main.db.save_conversation_state')
    @patch('app.main.db.add_message_to_conversation')
    @patch('app.main.db.save_survey_response')
    def test_yes_feedback_flow(self, mock_save_survey, mock_add_message, mock_save_state,
                               mock_get_survey, mock_get_customer, mock_get_conversation):
        """Test the 'Yes' response to feedback question."""
        # Setup for feedback question
        mock_get_conversation.return_value = {
            "id": "test-id",
            "customer_id": "1",
            "survey_id": "1",
            "current_question_index": 1,
            "answers": {"q1": "2"},
            "messages": [],
            "status": "active"
        }

        mock_get_customer.return_value = {"name": "John Doe"}

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

        mock_add_message.return_value = True
        mock_save_state.return_value = None

        # Call the function with "Yes please"
        process_user_response("test-id", "Yes please",
                              mock_get_conversation.return_value)

        # Verify awaiting_detailed_feedback flag was set
        assert mock_save_state.called
        call_args = mock_save_state.call_args[0]
        assert call_args[1]["awaiting_detailed_feedback"] == True

        # Verify prompt for detailed feedback
        assert mock_add_message.called
        message_args = mock_add_message.call_args[0]
        assert "share your thoughts" in message_args[2]

        # Now test the detailed feedback response
        mock_get_conversation.return_value = {
            "id": "test-id",
            "customer_id": "1",
            "survey_id": "1",
            "current_question_index": 1,
            "answers": {"q1": "2", "q2": "Yes please"},
            "messages": [],
            "status": "active",
            "awaiting_detailed_feedback": True
        }

        # Reset mocks
        mock_add_message.reset_mock()
        mock_save_state.reset_mock()

        # Call with detailed feedback
        process_user_response("test-id", "I love chocolate!",
                              mock_get_conversation.return_value)

        # Verify detailed feedback was saved
        assert mock_save_state.called
        call_args = mock_save_state.call_args[0]
        assert call_args[1]["answers"]["detailed_feedback"] == "I love chocolate!"
        assert call_args[1]["awaiting_detailed_feedback"] == False
        assert call_args[1]["status"] == "completed"

        # Verify completion message
        assert mock_add_message.called
        message_args = mock_add_message.call_args[0]
        assert "Thank you for your feedback" in message_args[2]

        # Verify survey response was saved
        assert mock_save_survey.called
