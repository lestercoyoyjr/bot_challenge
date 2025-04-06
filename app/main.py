from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import time
from datetime import datetime
import traceback

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

# Helper function with retry logic for RPC calls


def with_retry(func, *args, max_retries=3, **kwargs):
    """Execute a function with retry logic for RPC calls."""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except ConnectionError as e:
            if attempt < max_retries - 1:
                backoff = 0.5 * (2 ** attempt)  # Exponential backoff
                print(
                    f"RPC connection error on attempt {attempt+1}/{max_retries}, retrying in {backoff:.2f}s: {e}")
                time.sleep(backoff)
            else:
                print(f"Failed after {max_retries} attempts: {e}")
                raise
    return None

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
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(
                        f"Sending first message for conversation {conv_id}, attempt {attempt+1}/{max_retries}")
                    first_question = surv["questions"][0]
                    message = format_bot_message(cust["name"], first_question)
                    result = with_retry(
                        db.add_message_to_conversation, conv_id, "BOT", message)
                    print(
                        f"First message sent for conversation {conv_id}, result: {result}")
                    return
                except ConnectionError as e:
                    if attempt == max_retries - 1:
                        print(
                            f"Failed to send first message after {max_retries} attempts: {e}")
                except Exception as e:
                    print(f"Error sending first message: {e}")
                    traceback.print_exc()
                    break  # Don't retry on non-connection errors

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
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(
                        f"Processing response '{response}' for conversation {conv_id}, attempt {attempt+1}/{max_retries}")

                    # Get updated conversation state after user message
                    conv = with_retry(db.get_conversation_state, conv_id)
                    if not conv:
                        print(f"Conversation {conv_id} not found")
                        return

                    # Check if we're awaiting detailed feedback from a previous interaction
                    if conv.get("awaiting_detailed_feedback", False):
                        # Get customer information
                        customer = with_retry(
                            db.get_customer_info, conv["customer_id"])
                        if not customer:
                            print(f"Customer {conv['customer_id']} not found")
                            return

                        # Store the detailed feedback
                        conv["answers"]["detailed_feedback"] = response
                        conv["awaiting_detailed_feedback"] = False
                        with_retry(db.save_conversation_state, conv_id, conv)
                        print(f"Received detailed feedback: {response}")

                        # Thank the user for their feedback and complete the survey
                        completion_message = f"Thank you for your feedback, {customer['name']}! Your detailed response has been recorded. Have a wonderful day!"
                        result = with_retry(
                            db.add_message_to_conversation, conv_id, "BOT", completion_message)
                        print(
                            f"Sent completion message with feedback acknowledgment: {completion_message}, result: {result}")

                        # Mark survey as completed
                        conv["status"] = "completed"
                        with_retry(db.save_conversation_state, conv_id, conv)

                        # Save the survey response
                        survey_response = {
                            "conversation_id": conv_id,
                            "customer_id": conv["customer_id"],
                            "survey_id": conv["survey_id"],
                            "answers": conv["answers"],
                            "completed_at": datetime.now().isoformat()
                        }
                        with_retry(db.save_survey_response, survey_response)
                        print(
                            f"Saved survey response with detailed feedback: {survey_response}")
                        return

                    # Get customer information
                    customer = with_retry(
                        db.get_customer_info, conv["customer_id"])
                    if not customer:
                        print(f"Customer {conv['customer_id']} not found")
                        return

                    # Get survey information
                    survey = with_retry(db.get_survey_by_id, conv["survey_id"])
                    if not survey:
                        print(f"Survey {conv['survey_id']} not found")
                        return

                    # Save the user's answer
                    current_question_idx = conv.get(
                        "current_question_index", 0)
                    print(
                        f"Processing question at index {current_question_idx}")

                    try:
                        current_question = survey["questions"][current_question_idx]
                        print(f"Current question: {current_question['text']}")
                    except IndexError:
                        print(
                            f"Question index {current_question_idx} is out of bounds")
                        return

                    # Store the user's response
                    conv["answers"][current_question["id"]] = response
                    print(
                        f"Stored answer for question {current_question['id']}: {response}")

                    # Handle feedback question specifically
                    if current_question["id"] == "q2":
                        # Check if the response indicates user wants to provide feedback
                        positive_responses = ["yes", "yes please", "sure", "ok", "okay",
                                              "of course", "certainly", "definitely", "absolutely", "yeah"]
                        if any(pos in response.lower() for pos in positive_responses):
                            print(
                                "User indicated they would like to provide feedback")

                            # Ask for detailed feedback
                            feedback_message = "Great! Please share your thoughts about why you selected this flavor."
                            result = with_retry(
                                db.add_message_to_conversation, conv_id, "BOT", feedback_message)
                            print(
                                f"Asked for detailed feedback: {feedback_message}, result: {result}")

                            # Add another question to the survey dynamically (or handle as a sub-state)
                            # For this example, we'll create a special state to indicate we're awaiting detailed feedback
                            conv["awaiting_detailed_feedback"] = True
                            with_retry(db.save_conversation_state,
                                       conv_id, conv)
                            return
                        else:
                            # User doesn't want to provide feedback, proceed to completion
                            print(
                                "User declined to provide feedback, completing survey")

                    # Determine if we've reached the end of the survey
                    next_question_idx = current_question_idx + 1
                    print(f"Next question index would be: {next_question_idx}")
                    print(f"Total questions: {len(survey['questions'])}")

                    if next_question_idx >= len(survey["questions"]):
                        print("Reached end of survey, marking as completed")
                        # Survey complete
                        conv["status"] = "completed"
                        with_retry(db.save_conversation_state, conv_id, conv)
                        print(f"Saved conversation state with status 'completed'")

                        # Save the survey response
                        survey_response = {
                            "conversation_id": conv_id,
                            "customer_id": conv["customer_id"],
                            "survey_id": conv["survey_id"],
                            "answers": conv["answers"],
                            "completed_at": datetime.now().isoformat()
                        }
                        with_retry(db.save_survey_response, survey_response)
                        print(f"Saved survey response: {survey_response}")

                        # Send completion message
                        completion_message = f"Thank you for your time, {customer['name']}! Your response has been recorded. Have a wonderful day!"
                        result = with_retry(
                            db.add_message_to_conversation, conv_id, "BOT", completion_message)
                        print(
                            f"Sent completion message: {completion_message}, result: {result}")
                        return

                    # Move to the next question
                    print(
                        f"Moving to next question at index {next_question_idx}")
                    conv["current_question_index"] = next_question_idx
                    with_retry(db.save_conversation_state, conv_id, conv)
                    print(f"Updated conversation state with new question index")

                    # If the previous question was about flavor choice and user provided a choice
                    if current_question["id"] == "q1" and response in ["1", "2", "3"]:
                        print(f"Processing flavor choice: {response}")
                        # Get flavor name based on user's choice
                        flavor_choice = None
                        for option in current_question["options"]:
                            if option["id"] == response:
                                flavor_choice = option["text"]
                                break

                        if flavor_choice:
                            print(f"Selected flavor: {flavor_choice}")
                            # Send acknowledgment message for the flavor choice
                            ack_message = f"Great choice! {flavor_choice} is a classic favorite. Would you like to provide feedback on why you selected this flavor?"
                            result = with_retry(
                                db.add_message_to_conversation, conv_id, "BOT", ack_message)
                            print(
                                f"Sent acknowledgment message for {flavor_choice}: {ack_message}, result: {result}")
                            return
                        else:
                            print(f"No flavor found for choice: {response}")

                    # For other questions or if flavor not found, send the next question
                    try:
                        next_question = survey["questions"][next_question_idx]
                        print(f"Next question: {next_question['text']}")
                        next_message = format_bot_message(
                            customer["name"], next_question)
                        result = with_retry(
                            db.add_message_to_conversation, conv_id, "BOT", next_message)
                        print(
                            f"Sent next question: {next_message}, result: {result}")
                    except IndexError:
                        print(
                            f"No question found at index {next_question_idx}")

                    # Successfully processed, exit the retry loop
                    return

                except ConnectionError as e:
                    if attempt == max_retries - 1:
                        print(
                            f"Failed to process response after {max_retries} attempts: {e}")
                    # Will retry on next iteration if not the last attempt
                except Exception as e:
                    print(f"Error processing user response: {e}")
                    traceback.print_exc()
                    break  # Don't retry on non-connection errors

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


@app.get("/customers/{customer_id}/active-surveys")
async def get_active_surveys(customer_id: str):
    """Get all active/incomplete surveys for a customer."""
    try:
        # Check if customer exists
        customer = db.get_customer_info(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )

        # Get all active surveys for the customer
        active_surveys = db.get_customer_active_surveys(customer_id)

        # Format the response
        formatted_surveys = []
        for survey in active_surveys:
            # Get the survey details
            survey_details = db.get_survey_by_id(survey["survey_id"])

            # Calculate progress
            total_questions = len(
                survey_details["questions"]) if survey_details else 0
            current_question = survey["current_question_index"]
            progress = (current_question / total_questions) * \
                100 if total_questions > 0 else 0

            formatted_surveys.append({
                "conversation_id": survey["id"],
                "survey_id": survey["survey_id"],
                "survey_name": survey_details["name"] if survey_details else "Unknown Survey",
                "started_at": survey["created_at"],
                "last_updated": survey["updated_at"],
                "progress": progress,
                "current_question_index": current_question,
                "total_questions": total_questions
            })

        return formatted_surveys
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


@app.post("/conversations/{conversation_id}/resume")
async def resume_survey(
    conversation_id: str,
    background_tasks: BackgroundTasks
):
    """Resume a previously started survey conversation."""
    try:
        # Resume the conversation
        conversation = db.resume_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active conversation with ID {conversation_id} not found"
            )

        # Get necessary information
        customer_id = conversation["customer_id"]
        survey_id = conversation["survey_id"]

        # Get customer and survey information
        customer = db.get_customer_info(customer_id)
        survey = db.get_survey_by_id(survey_id)

        if not customer or not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer or survey information not found"
            )

        # Send a resume message in the background
        def send_resume_message(conv_id, cust, surv, conv):
            try:
                current_question_idx = conv["current_question_index"]
                current_question = surv["questions"][current_question_idx]

                # Create a resume message
                resume_message = f"Welcome back, {cust['name']}! Let's continue your survey.\n\n"
                resume_message += format_bot_message(
                    cust["name"], current_question)

                # Add the message to the conversation
                with_retry(db.add_message_to_conversation,
                           conv_id, "BOT", resume_message)

                print(f"Sent resume message for conversation {conv_id}")
            except Exception as e:
                print(f"Error sending resume message: {e}")
                traceback.print_exc()

        # Add the background task
        background_tasks.add_task(
            send_resume_message, conversation_id, customer, survey, conversation
        )

        return {"status": "resumed", "conversation_id": conversation_id}
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
