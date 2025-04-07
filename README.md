# Survey Chatbot System Documentation

## Overview

The Survey Chatbot System is a FastAPI-based application designed to conduct automated surveys with users through a conversational interface. It offers both RESTful API endpoints and real-time WebSocket communication for interactive survey experiences.

## System Architecture

### Components

1. **FastAPI Backend**

   - Manages survey logic and conversation state
   - Provides RESTful API endpoints
   - Handles WebSocket connections for real-time communication

2. **Mock Database Layer**

   - Simulates database operations with RPC-like interactions
   - Handles storage of surveys, customer data, and conversation states
   - Implements artificial network latency and failure scenarios for testing

3. **WebSocket Client**
   - Browser-based test client for interacting with the survey chatbot
   - Supports session persistence and reconnection attempts

### Data Models

- **Conversations**: Tracks active survey sessions, including current question, answers, and status
- **Customers**: Stores customer information
- **Surveys**: Defines survey structure including questions and answer options
- **Survey Responses**: Records completed survey submissions

## API Reference

### REST Endpoints

| Endpoint                                    | Method | Description                             |
| ------------------------------------------- | ------ | --------------------------------------- |
| `/health`                                   | GET    | Health check endpoint                   |
| `/surveys`                                  | GET    | Retrieve all available surveys          |
| `/surveys/{survey_id}`                      | GET    | Get a specific survey by ID             |
| `/conversations`                            | POST   | Start a new conversation/survey session |
| `/conversations/{conversation_id}`          | GET    | Get the state of a conversation         |
| `/conversations/{conversation_id}/messages` | GET    | Get all messages for a conversation     |
| `/conversations/{conversation_id}/messages` | POST   | Send a message to a conversation        |
| `/conversations/{conversation_id}/resume`   | POST   | Resume a previously started survey      |
| `/customers/{customer_id}/active-surveys`   | GET    | List all active surveys for a customer  |

### WebSocket Interface

- **Endpoint**: `/ws/{conversation_id}`
- **Purpose**: Real-time bidirectional communication for survey interactions
- **Features**:
  - Initial state synchronization
  - Message history retrieval
  - Automatic reconnection handling
  - Survey completion notification

## Error Handling

The system implements:

1. **RPC Error Handling**

   - Retry logic with exponential backoff
   - Maximum retry limits
   - Graceful failure reporting

2. **WebSocket Connection Management**
   - Reconnection attempts for dropped connections
   - Session state persistence
   - Error notification to clients

## Setup and Deployment

### Requirements

- Python 3.10 or higher
- Dependencies managed through Poetry

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd survey-chatbot

# Install dependencies using Poetry
poetry install

# Start the application
poetry run python -m app.main
```

### Development Environment

The project uses Poetry for dependency management:

- FastAPI for the web framework
- Uvicorn as the ASGI server
- Pytest for testing

## Testing

The system can be tested through:

1. **Automated Tests**

   - Unit tests for database operations
   - Integration tests for API endpoints
   - WebSocket connection tests

2. **Manual Testing Client**
   - Browser-based WebSocket client in `test_websocket.html`
   - Supports connection management and message sending

## Flow of Operation

### Survey Initiation

1. Client requests to start a survey via `/conversations` endpoint
2. Server creates a conversation and sends the first question
3. Client connects to the WebSocket endpoint to receive real-time updates

### Survey Progression

1. Client sends responses through WebSocket or REST API
2. Server processes the answer and updates the conversation state
3. Server sends the next question or follow-up based on the survey flow
4. Special handling for open-ended feedback questions

### Survey Completion

1. Server marks the conversation as completed when all questions are answered
2. Survey responses are saved to the database
3. Client is notified of survey completion
4. WebSocket connection is gracefully closed

## Implementation Details

### Mock Database

The system uses an in-memory mock database that simulates network latency and potential failures to test resilience:

- Conversations are stored with their complete state
- Network latency is simulated with random delays
- Occasional failures are introduced to test error handling
- All database access is performed via RPC-like calls

### Background Tasks

The system leverages FastAPI's background tasks for asynchronous operations:

- Sending initial survey questions
- Processing user responses
- Handling follow-up questions based on user input

### WebSocket Connection Management

The system implements a connection manager to handle multiple concurrent WebSocket connections:

- Tracks active connections by conversation ID
- Handles client disconnections gracefully
- Supports broadcasting messages to specific conversations
- Implements reconnection protocols for network interruptions

## Security Considerations

While this implementation is primarily for demonstration purposes, a production system would need:

1. Authentication and authorization
2. Rate limiting
3. Input validation and sanitization
4. HTTPS/WSS secure connections
5. Data encryption at rest and in transit

## Future Enhancements

Potential improvements include:

1. Persistent database storage
2. Analytics dashboard for survey results
3. More complex survey logic with branching
4. Multi-language support
5. Integration with messaging platforms
6. AI-powered response analysis
