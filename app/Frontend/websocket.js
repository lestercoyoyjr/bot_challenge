let socket;
let reconnectAttempts = 0;
let maxReconnectAttempts = 3;
let reconnectTimeout;
let surveyCompleted = false;

function setConnectionStatus(connected) {
    const connectBtn = document.getElementById("connect-btn");
    const disconnectBtn = document.getElementById("disconnect-btn");
    const messageInput = document.getElementById("message");
    const sendBtn = document.getElementById("send-btn");
    const statusDiv = document.getElementById("connection-status");

    if (connected) {
        connectBtn.disabled = true;
        disconnectBtn.disabled = false;
        messageInput.disabled = surveyCompleted;
        sendBtn.disabled = surveyCompleted;
        statusDiv.className = "status connected";
        statusDiv.textContent = "Connected";
    } else {
        connectBtn.disabled = false;
        disconnectBtn.disabled = true;
        messageInput.disabled = true;
        sendBtn.disabled = true;
        statusDiv.className = "status disconnected";
        statusDiv.textContent = "Disconnected";
    }
}

function addMessage(message, type) {
    const messagesDiv = document.getElementById("messages");
    const messageElement = document.createElement("div");
    messageElement.className = type;
    messageElement.textContent = message;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function connect(isReconnect = false) {
    const conversationId = document.getElementById("conversation-id").value;

    if (!conversationId) {
        addMessage("Please enter a conversation ID", "error");
        return;
    }

    // Clear previous messages if not reconnecting
    if (!isReconnect) {
        document.getElementById("messages").innerHTML = "";
        surveyCompleted = false;
    }

    // Create WebSocket connection
    let wsUrl = `ws://localhost:8000/ws/${conversationId}`;
    if (isReconnect) {
        wsUrl += "?reconnect=true";
    }

    socket = new WebSocket(wsUrl);

    socket.onopen = function (e) {
        addMessage("Connected to server", "system");
        setConnectionStatus(true);

        // Send reconnection confirmation if reconnecting
        if (isReconnect) {
            socket.send(JSON.stringify({ type: "reconnect_confirm" }));
        }

        // Reset reconnect attempts on successful connection
        reconnectAttempts = 0;
    };

    socket.onmessage = function (event) {
        try {
            const data = JSON.parse(event.data);

            // Handle different message types
            if (data.type === "error") {
                addMessage(`Error: ${data.message}`, "error");
            } else if (data.type === "state") {
                addMessage("Received initial state", "system");
                console.log("State:", data);
            } else if (data.type === "history") {
                addMessage("Received message history", "system");
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach((msg) => {
                        addMessage(
                            `${msg.sender}: ${msg.content}`,
                            msg.sender.toLowerCase()
                        );
                    });
                } else {
                    addMessage("No message history", "system");
                }
            } else if (data.type === "message") {
                addMessage(
                    `${data.sender}: ${data.content}`,
                    data.sender.toLowerCase()
                );
            } else if (data.type === "resumed") {
                addMessage(`Resumed conversation: ${data.message}`, "system");
            } else if (data.type === "completed") {
                addMessage(`Survey completed: ${data.message}`, "system");
                surveyCompleted = true;

                // Disable message input when survey is completed
                document.getElementById("message").disabled = true;
                document.getElementById("send-btn").disabled = true;

                if (data.close_connection) {
                    addMessage(
                        `Connection will close: ${data.close_reason}`,
                        "system"
                    );
                }
            } else if (data.type === "reconnect_success") {
                addMessage(`Reconnection successful: ${data.message}`, "system");
            } else {
                addMessage(`Received: ${JSON.stringify(data)}`, "system");
            }
        } catch (e) {
            addMessage(`Failed to parse message: ${event.data}`, "error");
        }
    };

    socket.onclose = function (event) {
        setConnectionStatus(false);

        if (surveyCompleted) {
            addMessage(`Connection closed: Survey completed`, "system");
            return; // Don't attempt to reconnect if survey is completed
        }

        if (event.wasClean) {
            addMessage(
                `Connection closed cleanly, code=${event.code}, reason=${event.reason}`,
                "system"
            );
        } else {
            addMessage("Connection died", "error");

            // Attempt to reconnect
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                const timeout = Math.min(
                    1000 * Math.pow(2, reconnectAttempts),
                    10000
                );

                addMessage(
                    `Attempting to reconnect in ${timeout / 1000
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
        }
    };

    socket.onerror = function (error) {
        addMessage(`WebSocket error occurred`, "error");
        console.error("WebSocket error:", error);
    };
}

function disconnect() {
    if (socket) {
        socket.close(1000, "User initiated disconnect");
        addMessage("Disconnected from server", "system");
        setConnectionStatus(false);

        // Clear any pending reconnect attempts
        clearTimeout(reconnectTimeout);
    }
}

function sendMessage() {
    const messageInput = document.getElementById("message");
    const message = messageInput.value;

    if (!message) {
        addMessage("Please enter a message", "error");
        return;
    }

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        addMessage("Not connected to server", "error");
        return;
    }

    // Send message
    const messageObj = { content: message };
    socket.send(JSON.stringify(messageObj));

    // Add message to display
    addMessage(`USER: ${message}`, "user");

    // Clear input
    messageInput.value = "";
}

// Allow pressing Enter to send a message
document
    .getElementById("message")
    .addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            sendMessage();
        }
    });

// Set initial connection status
setConnectionStatus(false);