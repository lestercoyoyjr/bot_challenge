from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import time
from datetime import datetime

from app.db import MockRPCDatabase

app = FastAPI(title="Survey Chatbot API")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you'd specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database instance
db = MockRPCDatabase()

# Pydantic models for request/response validation


class Message(BaseModel):
    sender: str  # "BOT" or "USER"
    content: str
    timestamp: str


class ConversationState(BaseModel):
    id: str
    customer_id: str
    survey_id: str
    current_question_index: int
    answers: Dict[str, Any]
    messages: List[Message]
    status: str
    created_at: str
    updated_at: str


class StartConversationRequest(BaseModel):
    customer_id: str
    survey_id: str


class MessageRequest(BaseModel):
    content: str


class SurveyOption(BaseModel):
    id: str
    text: str


class SurveyQuestion(BaseModel):
    id: str
    text: str
    options: List[SurveyOption]


class Survey(BaseModel):
    id: str
    name: str
    questions: List[SurveyQuestion]

# Exception handling for RPC failures


def handle_rpc_error(func):
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Database service is currently unavailable. Please try again later."
                    )
                time.sleep(0.5)  # Wait before retrying
    return wrapper

# Helper function to format bot messages


def format_bot_message(customer_name: str, survey_question: dict) -> str:
    if not survey_question.get("options"):
        return f"Would you like to provide feedback on why you selected this option?"

    options_text = "\n".join(
        [f"{option['id']} - {option['text']}" for option in survey_question["options"]])
    return f"Hello {customer_name}! {survey_question['text']}\nHere are your options:\n{options_text}\n\nPlease reply with the number corresponding to your choice."

# Health check endpoint


@app.get("/health")
async def health():
    return {"healthy": True}

# Get all available surveys


@app.get("/surveys")
async def get_surveys():
    """Get all available surveys."""
    try:
        return db.get_all_surveys()
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@app.get("/surveys/{survey_id}")
async def get_survey(survey_id: str):
    """Get a specific survey by ID."""
    try:
        survey = db.get_survey_by_id(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Survey with ID {survey_id} not found"
            )
        return survey
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Start a new conversation


@app.post("/conversations", status_code=status.HTTP_201_CREATED)
async def start_conversation(
    request: StartConversationRequest,
    background_tasks: BackgroundTasks
):
    """Start a new conversation with a customer for a survey."""
    try:
        customer_id = request.customer_id
        survey_id = request.survey_id

        # Get customer information
        customer = db.get_customer_info(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )

        # Get survey information
        survey = db.get_survey_by_id(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Survey with ID {survey_id} not found"
            )

        # Create a new conversation
        conversation_id = db.create_conversation(customer_id, survey_id)

        # Send the first message in the background
        def send_first_message(conv_id, cust, surv):
            try:
                first_question = surv["questions"][0]
                message = format_bot_message(cust["name"], first_question)
                db.add_message_to_conversation(conv_id, "BOT", message)
            except Exception as e:
                print(f"Error sending first message: {e}")

        background_tasks.add_task(
            send_first_message, conversation_id, customer, survey)

        return {"conversation_id": conversation_id}
    except ConnectionError:
        # Handle RPC error
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
# Get conversation state


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get the state of a conversation."""
    try:
        conversation = db.get_conversation_state(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with ID {conversation_id} not found"
            )
        return conversation
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Get conversation messages


@app.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    """Get all messages for a conversation."""
    try:
        messages = db.get_conversation_messages(conversation_id)
        return messages
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Send a message to a conversation


@app.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    message: MessageRequest,
    background_tasks: BackgroundTasks
):
    """Send a message to a conversation."""
    try:
        # Get conversation state
        conversation = db.get_conversation_state(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with ID {conversation_id} not found"
            )

        # Add user message to conversation
        success = db.add_message_to_conversation(
            conversation_id, "USER", message.content)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add message to conversation"
            )

        # Process user's response and continue the survey flow
        def process_user_response(conv_id, response, conv):
            try:
                # Get updated conversation state after user message
                conv = db.get_conversation_state(conv_id)
                if not conv:
                    return

                # Get customer information
                customer = db.get_customer_info(conv["customer_id"])
                if not customer:
                    return

                # Get survey information
                survey = db.get_survey_by_id(conv["survey_id"])
                if not survey:
                    return

                # Save the user's answer
                current_question_idx = conv.get("current_question_index", 0)
                current_question = survey["questions"][current_question_idx]

                # Store the user's response
                conv["answers"][current_question["id"]] = response

                # Determine if we've reached the end of the survey
                next_question_idx = current_question_idx + 1
                if next_question_idx >= len(survey["questions"]):
                    # Survey complete
                    conv["status"] = "completed"
                    db.save_conversation_state(conv_id, conv)

                    # Save the survey response
                    survey_response = {
                        "conversation_id": conv_id,
                        "customer_id": conv["customer_id"],
                        "survey_id": conv["survey_id"],
                        "answers": conv["answers"],
                        "completed_at": datetime.now().isoformat()
                    }
                    db.save_survey_response(survey_response)

                    # Send completion message
                    completion_message = f"Thank you for your time, {customer['name']}! Your response has been recorded. Have a wonderful day!"
                    db.add_message_to_conversation(
                        conv_id, "BOT", completion_message)
                    return

                # Move to the next question
                conv["current_question_index"] = next_question_idx
                db.save_conversation_state(conv_id, conv)

                # If the previous question was about flavor choice and user provided a choice
                if current_question["id"] == "q1" and response in ["1", "2", "3"]:
                    # Get flavor name based on user's choice
                    flavor_choice = None
                    for option in current_question["options"]:
                        if option["id"] == response:
                            flavor_choice = option["text"]
                            break

                    if flavor_choice:
                        # Send acknowledgment message for the flavor choice
                        ack_message = f"Great choice! {flavor_choice} is a classic favorite. Would you like to provide feedback on why you selected this flavor?"
                        db.add_message_to_conversation(
                            conv_id, "BOT", ack_message)
                        return

                # For other questions or if flavor not found, send the next question
                next_question = survey["questions"][next_question_idx]
                next_message = format_bot_message(
                    customer["name"], next_question)
                db.add_message_to_conversation(conv_id, "BOT", next_message)
            except Exception as e:
                print(f"Error processing user response: {e}")

        # Process the user's response in the background
        background_tasks.add_task(
            process_user_response, conversation_id, message.content, conversation)

        return {"status": "message received"}
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


def main():
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()
