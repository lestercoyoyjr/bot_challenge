import time
import random
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

mock_db = {
    "conversations": {},
    "customers": {
        "1": {"name": "John Doe", "email": "john.doe@example.com"},
        "2": {"name": "Jane Smith", "email": "jane.smith@example.com"},
    },
    "surveys": [
        {
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
                    "text": "Would you like to provide feedback on why you selected this flavor?",
                    "options": []  # Open question
                }
            ]
        }
    ],
    "survey_responses": []
}

# Simulate network latency and possible failures


def simulate_rpc_call():
    time.sleep(random.uniform(0.1, 0.5))  # Simulate network delay
    # temporary disable random failures for testing
    # if random.random() < 0.1:  # 10% chance of failure
    #    raise ConnectionError("RPC call failed")


class MockRPCDatabase:
    """
    An example mock database.
    Adjust and customize this file as you wish, but assume all db access is via RPCs.
    """
    @staticmethod
    def get_conversation_state(conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the state of a conversation."""
        simulate_rpc_call()
        return mock_db["conversations"].get(conversation_id)

    @staticmethod
    def save_conversation_state(conversation_id: str, state: Dict[str, Any]) -> None:
        """Save or update the state of a conversation."""
        simulate_rpc_call()
        mock_db["conversations"][conversation_id] = state

    @staticmethod
    def get_customer_info(customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve customer information."""
        simulate_rpc_call()
        return mock_db["customers"].get(customer_id)

    @staticmethod
    def save_survey_response(response: Dict[str, Any]) -> None:
        """Save a survey response."""
        simulate_rpc_call()
        mock_db["survey_responses"].append(response)

    @staticmethod
    def get_all_surveys() -> List[Dict[str, Any]]:
        """Get all available surveys."""
        simulate_rpc_call()
        return mock_db["surveys"]

    @staticmethod
    def get_survey_by_id(survey_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific survey by ID."""
        simulate_rpc_call()
        for survey in mock_db["surveys"]:
            if survey["id"] == survey_id:
                return survey
        return None

    @staticmethod
    def create_conversation(customer_id: str, survey_id: str) -> str:
        """Create a new conversation for a survey with a customer."""
        simulate_rpc_call()
        conversation_id = str(uuid.uuid4())

        # Get customer info and survey
        customer = mock_db["customers"].get(customer_id)
        survey = None
        for s in mock_db["surveys"]:
            if s["id"] == survey_id:
                survey = s
                break

        if not customer or not survey:
            raise ValueError("Customer or survey not found")

        # Create initial conversation state
        mock_db["conversations"][conversation_id] = {
            "id": conversation_id,
            "customer_id": customer_id,
            "survey_id": survey_id,
            "current_question_index": 0,
            "answers": {},
            "messages": [],
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        return conversation_id

    @staticmethod
    def get_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation."""
        simulate_rpc_call()
        conversation = mock_db["conversations"].get(conversation_id)
        if not conversation:
            return []
        return conversation.get("messages", [])

    @staticmethod
    def add_message_to_conversation(conversation_id: str, sender: str, message: str) -> bool:
        """Add a message to a conversation."""
        simulate_rpc_call()
        conversation = mock_db["conversations"].get(conversation_id)
        if not conversation:
            return False

        # Add message to conversation
        message_obj = {
            "sender": sender,
            "content": message,
            "timestamp": datetime.now().isoformat()
        }

        if "messages" not in conversation:
            conversation["messages"] = []

        conversation["messages"].append(message_obj)
        conversation["updated_at"] = datetime.now().isoformat()

        # Update the conversation in the database
        mock_db["conversations"][conversation_id] = conversation
        return True
