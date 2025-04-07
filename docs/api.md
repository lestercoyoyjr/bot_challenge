# Survey Chatbot API Reference

## Base URL

All API endpoints are relative to the base URL: `http://localhost:8000/docs#/`

## Authentication

_Note: This implementation does not include authentication. In a production environment, authentication would be required._

## Data Models

### Message

```json
{
  "sender": "string", // "BOT" or "USER"
  "content": "string",
  "timestamp": "string" // ISO format
}
```

### ConversationState

```json
{
  "id": "string",
  "customer_id": "string",
  "survey_id": "string",
  "current_question_index": 0,
  "answers": {},
  "messages": [],
  "status": "string", // "active" or "completed"
  "created_at": "string", // ISO format
  "updated_at": "string" // ISO format
}
```

### Survey

```json
{
  "id": "string",
  "name": "string",
  "questions": [
    {
      "id": "string",
      "text": "string",
      "options": [
        {
          "id": "string",
          "text": "string"
        }
      ]
    }
  ]
}
```

## REST Endpoints

### Health Check

```
GET /health
```

Returns the health status of the API service.

**Response (200 OK)**

```json
{
  "healthy": true
}
```

### Surveys

#### Get All Surveys

```
GET /surveys
```

Retrieves a list of all available surveys.

**Response (200 OK)**

```json
[
  {
    "id": "1",
    "name": "Ice Cream Preference",
    "questions": [
      {
        "id": "q1",
        "text": "Which flavor of ice cream do you prefer?",
        "options": [
          { "id": "1", "text": "Vanilla" },
          { "id": "2", "text": "Chocolate" },
          { "id": "3", "text": "Strawberry" }
        ]
      },
      {
        "id": "q2",
        "text": "Would you like to provide feedback on why you selected this flavor?",
        "options": []
      }
    ]
  }
]
```

#### Get Survey by ID

```
GET /surveys/{survey_id}
```

Retrieves a specific survey by its ID.

**Parameters**

- `survey_id` (path): The ID of the survey to retrieve

**Response (200 OK)**

```json
{
  "id": "1",
  "name": "Ice Cream Preference",
  "questions": [
    {
      "id": "q1",
      "text": "Which flavor of ice cream do you prefer?",
      "options": [
        { "id": "1", "text": "Vanilla" },
        { "id": "2", "text": "Chocolate" },
        { "id": "3", "text": "Strawberry" }
      ]
    }
  ]
}
```

**Error Responses**

- `404 Not Found`: Survey with specified ID not found
- `503 Service Unavailable`: Database service unavailable

### Conversations

#### Start a New Conversation

```
POST /conversations
```

Starts a new survey conversation with a customer.

**Request Body**

```json
{
  "customer_id": "string",
  "survey_id": "string"
}
```

**Response (201 Created)**

```json
{
  "conversation_id": "string"
}
```

**Error Responses**

- `404 Not Found`: Customer or survey not found
- `503 Service Unavailable`: Database service unavailable

#### Get Conversation State

```
GET /conversations/{conversation_id}
```

Retrieves the current state of a conversation.

**Parameters**

- `conversation_id` (path): The ID of the conversation

**Response (200 OK)**

```json
{
  "id": "string",
  "customer_id": "string",
  "survey_id": "string",
  "current_question_index": 0,
  "answers": {},
  "messages": [],
  "status": "active",
  "created_at": "string",
  "updated_at": "string"
}
```

**Error Responses**

- `404 Not Found`: Conversation not found
- `503 Service Unavailable`: Database service unavailable

#### Get Conversation Messages

```
GET /conversations/{conversation_id}/messages
```

Retrieves all messages for a specific conversation.

**Parameters**

- `conversation_id` (path): The ID of the conversation

**Response (200 OK)**

```json
[
  {
    "sender": "BOT",
    "content": "Hello John! Which flavor of ice cream do you prefer?",
    "timestamp": "2023-05-10T14:23:05.123456"
  },
  {
    "sender": "USER",
    "content": "2",
    "timestamp": "2023-05-10T14:23:15.654321"
  }
]
```

**Error Responses**

- `503 Service Unavailable`: Database service unavailable

#### Send Message to Conversation

```
POST /conversations/{conversation_id}/messages
```

Sends a new message to a conversation.

**Parameters**

- `conversation_id` (path): The ID of the conversation

**Request Body**

```json
{
  "content": "string"
}
```

**Response (201 Created)**

```json
{
  "status": "message received"
}
```

**Error Responses**

- `404 Not Found`: Conversation not found
- `503 Service Unavailable`: Database service unavailable

#### Resume a Conversation

```
POST /conversations/{conversation_id}/resume
```

Resumes a previously started conversation.

**Parameters**

- `conversation_id` (path): The ID of the conversation to resume

**Response (200 OK)**

```json
{
  "status": "resumed",
  "conversation_id": "string"
}
```

**Error Responses**

- `404 Not Found`: Conversation not found or already completed
- `503 Service Unavailable`: Database service unavailable

#### Get Customer's Active Surveys

```
GET /customers/{customer_id}/active-surveys
```

Retrieves all active surveys for a specific customer.

**Parameters**

- `customer_id` (path): The ID of the customer

**Response (200 OK)**

```json
[
  {
    "conversation_id": "string",
    "survey_id": "string",
    "survey_name": "string",
    "started_at": "string",
    "last_updated": "string",
    "progress": 50.0,
    "current_question_index": 1,
    "total_questions": 2
  }
]
```

**Error Responses**

- `404 Not Found`: Customer not found
- `503 Service Unavailable`: Database service unavailable

## WebSocket Interface

### Connect to Survey WebSocket

```
WebSocket: ws://localhost:8000/ws/{conversation_id}
```

Establishes a WebSocket connection for real-time survey interaction.

**Parameters**

- `conversation_id` (path): The ID of the conversation
- `reconnect=true` (query, optional): Flag to indicate a reconnection attempt

### WebSocket Message Types

#### Client to Server

Messages sent from client to server should be JSON objects with the following structure:

```json
{
  "content": "string" // The message content (e.g., survey answer)
}
```

For reconnection confirmation:

```json
{
  "type": "reconnect_confirm"
}
```

#### Server to Client

1. **State Message**

   ```json
   {
     "type": "state",
     "conversation": {...},  // ConversationState object
     "customer": {...},      // Customer information
     "survey": {...}         // Survey object
   }
   ```

2. **History Message**

   ```json
   {
     "type": "history",
     "messages": [...]  // Array of Message objects
   }
   ```

3. **Chat Message**

   ```json
   {
     "type": "message",
     "sender": "BOT", // or "USER"
     "content": "string",
     "timestamp": "string"
   }
   ```

4. **Error Message**

   ```json
   {
     "type": "error",
     "message": "string"
   }
   ```

5. **Resumed Message**

   ```json
   {
     "type": "resumed",
     "currentQuestion": {...},  // Question object
     "message": "string"
   }
   ```

6. **Completed Message**

   ```json
   {
     "type": "completed",
     "message": "string",
     "close_connection": true, // Optional
     "close_code": 1000, // Optional
     "close_reason": "string" // Optional
   }
   ```

7. **Reconnection Success Message**
   ```json
   {
     "type": "reconnect_success",
     "message": "string"
   }
   ```
