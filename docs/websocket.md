# WebSocket Protocol Documentation

## Overview

The Survey Chatbot implements a real-time communication protocol using WebSockets to enable interactive survey experiences. This document details the WebSocket implementation, message protocol, connection management, and error handling mechanisms.

## Connection Establishment

### Endpoint

```
ws://localhost:8000/ws/{conversation_id}
```

Where `{conversation_id}` is the unique identifier for a specific survey conversation.

### Connection Parameters

- `reconnect=true` (query parameter, optional): Indicates that this is a reconnection attempt after a connection loss.

### Connection Lifecycle

1. **Initial Connection**

   - Client attempts to connect to the WebSocket endpoint
   - Server validates the conversation ID
   - Upon successful validation, server accepts the connection
   - Server sends initial state and message history

2. **Reconnection**

   - Client attempts to reconnect with `reconnect=true` parameter
   - Client sends `reconnect_confirm` message after successful reconnection
   - Server responds with `reconnect_success` message
   - Server resynchronizes the conversation state

3. **Disconnection**
   - Graceful disconnection when survey is completed
   - Automatic reconnection attempts for unexpected disconnections
   - Maximum reconnection attempts with exponential backoff

## Message Protocol

### Client to Server Messages

Messages sent from the client to the server should be formatted as JSON objects.

**Standard Message**

```json
{
  "content": "User's response to the survey question"
}
```

**Reconnection Confirmation**

```json
{
  "type": "reconnect_confirm"
}
```

### Server to Client Messages

The server sends multiple types of messages to provide information and guide the client through the survey process.

#### State Message

Provides the current state of the conversation.

```json
{
  "type": "state",
  "conversation": {
    "id": "string",
    "customer_id": "string",
    "survey_id": "string",
    "current_question_index": 0,
    "answers": {},
    "messages": [],
    "status": "active",
    "created_at": "string",
    "updated_at": "string"
  },
  "customer": {
    "name": "string",
    "email": "string"
  },
  "survey": {
    "id": "string",
    "name": "string",
    "questions": [...]
  }
}
```

#### History Message

Provides the message history of the conversation.

```json
{
  "type": "history",
  "messages": [
    {
      "sender": "BOT",
      "content": "string",
      "timestamp": "string"
    },
    {
      "sender": "USER",
      "content": "string",
      "timestamp": "string"
    }
  ]
}
```

#### Message

Represents a single message in the conversation.

```json
{
  "type": "message",
  "sender": "BOT", // or "USER"
  "content": "string",
  "timestamp": "string"
}
```

#### Error Message

Indicates an error that occurred during processing.

```json
{
  "type": "error",
  "message": "Error description"
}
```

#### Resumed Message

Sent when a conversation is successfully resumed.

```json
{
  "type": "resumed",
  "currentQuestion": {
    "id": "string",
    "text": "string",
    "options": [...]
  },
  "message": "Resumed conversation message"
}
```

#### Completed Message

Indicates that the survey has been completed.

```json
{
  "type": "completed",
  "message": "Survey completion message",
  "close_connection": true, // Indicates connection will be closed
  "close_code": 1000, // WebSocket close code
  "close_reason": "Survey completed successfully" // Close reason
}
```

#### Reconnection Success Message

Confirms successful reconnection.

```json
{
  "type": "reconnect_success",
  "message": "Reconnection successful"
}
```

## Connection Manager

The server implements a connection manager that handles multiple concurrent WebSocket connections:

```python
class ConnectionManager:
    def __init__(self):
        # Store active connections by conversation_id
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            # Clean up empty lists
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def send_message(self, message: dict, conversation_id: str):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                await connection.send_json(message)

    async def broadcast(self, message: dict):
        # Send to all connected clients across all conversations
        for connections in self.active_connections.values():
            for connection in connections:
                await connection.send_json(message)
```

## Client-Side Implementation

The client-side implementation handles:

1. **Connection Management**

   - Establishing WebSocket connections
   - Handling disconnections
   - Implementing reconnection logic with exponential backoff

2. **Message Processing**

   - Parsing incoming messages
   - Displaying appropriate responses based on message type

3. **User Interface**
   - Updating UI with connection status
   - Displaying conversation history
   - Enabling/disabling input based on survey state

### Reconnection Strategy

The client implements a reconnection strategy with exponential backoff:

```javascript
if (reconnectAttempts < maxReconnectAttempts) {
  reconnectAttempts++;
  const timeout = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);

  addMessage(
    `Attempting to reconnect in ${
      timeout / 1000
    } seconds (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`,
    "system"
  );

  clearTimeout(reconnectTimeout);
  reconnectTimeout = setTimeout(() => {
    addMessage(`Reconnecting...`, "system");
    connect(true);
  }, timeout);
} else {
  addMessage(
    `Failed to reconnect after ${maxReconnectAttempts} attempts`,
    "error"
  );
}
```

## Survey Flow Diagram

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Connect to │      │ Receive     │      │ Send        │
│  WebSocket  │─────▶│ Initial     │─────▶│ Response    │
└─────────────┘      │ Question    │      │             │
                     └─────────────┘      └─────────────┘
                                                 │
                                                 ▼
                     ┌─────────────┐      ┌─────────────┐
                     │ Survey      │◀─────│ Process     │
                     │ Completed   │      │ Follow-up   │
                     └─────────────┘      │ Questions   │
                           ▲              └─────────────┘
                           │                     ▲
                           │                     │
                     ┌─────────────┐      ┌─────────────┐
                     │ Final       │      │ Receive     │
                     │ Question    │◀─────│ Next        │
                     │ Answered    │      │ Question    │
                     └─────────────┘      └─────────────┘
```

## Error Handling

### Server-Side Error Handling

1. **Connection Errors**

   - Graceful handling of connection failures
   - Proper cleanup of resources
   - Informative error messages sent to clients

2. **Processing Errors**
   - Retry logic for database operations
   - Error reporting through WebSocket messages
   - Transaction safety for partial updates

### Client-Side Error Handling

1. **Connection Issues**

   - Automatic reconnection attempts
   - User feedback on connection status
   - Exponential backoff to avoid overwhelming the server

2. **Message Parsing**
   - Robust JSON parsing with error handling
   - Fallback UI updates for unexpected message formats

## Testing the WebSocket Interface

The project includes a browser-based test client (`test_websocket.html`) that can be used to test the WebSocket interface:

1. Open the test client in a web browser
2. Enter a valid conversation ID
3. Click the "Connect" button to establish a WebSocket connection
4. Interact with the survey by sending responses
5. Observe the messages received from the server

The test client also demonstrates reconnection handling and displays connection status information.

## Security Considerations

In a production environment, consider implementing:

1. **Authentication**

   - Token-based authentication for WebSocket connections
   - Validation of client identity before allowing connections

2. **Transport Security**

   - WSS (WebSocket Secure) for encrypted communications
   - Proper certificate management

3. **Input Validation**

   - Sanitization of all user inputs
   - Message size limitations
   - Rate limiting for message frequency

4. **Connection Management**
   - Timeout for inactive connections
   - Maximum connections per client
   - Resource allocation limits
