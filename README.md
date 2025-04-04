# Coding Challenge Specification: **Survey Response Chatbot Server**

## Objective  
The purpose of this challenge is to assess your ability to design and implement a chatbot server that focuses on collecting survey responses from customers. Your implementation should demonstrate your problem-solving skills, technical strengths, and understanding of backend development principles. While the core task is to deliver a functional survey response chatbot, you are encouraged to add enhancements or optional features to showcase your engineering skills.

---

## Context  
Your task is to build a chatbot server that facilitates **real-time survey collection** from customers. This challenge focuses exclusively on the **API/backend implementation**. **No frontend development is required**. 

You will be provided with a skeleton repository containing a FastAPI project setup and some mock API endpoints. Database access is abstracted via mocked RPC calls, implemented in [db.py](./app/db.py).  
You must adjust [db.py](./app/db.py) as needed, but note that all database interactions must be handled through these mock RPC calls. This simulates accessing an external system and ensures that the solution remains generic.

## Example of conversation between a user and the bot
```
2024-01-12 10:00:00 BOT: Hello John Doe!  
We are interested to know which flavour of ice cream you prefer. Here are your options:  
1 - Vanilla  
2 - Chocolate  
3 - Strawberry  

Please reply with the number corresponding to your choice.  

2024-01-12 10:00:10 USER: 2  

2024-01-12 10:00:15 BOT: Great choice! Chocolate is a classic favorite.  
Would you like to provide feedback on why you selected this flavor?  

2024-01-12 10:00:30 USER: No, thank you.  

2024-01-12 10:00:35 BOT: Thank you for your time, John Doe!  
Your response has been recorded. Have a wonderful day!  
```

Feel free to use modern AI tools like ChatGPT to quickly generate mock data or
skeleton code.

---

## Requirements  

### 1. **Core Functionality: Survey Response Chatbot**
- Implement a chatbot server that:  
  - Guides customers through a survey, asking predefined questions.  
  - Collects and stores customer responses to survey questions via the mock RPC interface.  
  - Ensures survey progress and context are preserved across multiple interactions.  
  - Allows customers to resume partially completed surveys.  

### 2. **State Management**
- Design and implement a mechanism to manage survey states:
  - Track which questions have been answered.
  - Handle concurrent survey interactions with multiple customers.
  - Support reconnects or session continuity in case of temporary disconnects.

### 3. **Real-Time Communication**
- Support sending questions to customers and receiving responses in real time.
- Handle connection lifecycle events, such as client disconnection and reconnection.

### 4. **Error Handling**
- Implement robust error handling to manage:  
  - RPC call failures (e.g., retries or fallback responses).  
  - Invalid inputs or unexpected scenarios during survey interactions.  
  - Unrecoverable errors with meaningful feedback to customers.  

### 5. **Unit Tests**
- Write automated unit tests to ensure:  
  - Core functionalities (e.g., question flow, response collection) are thoroughly tested.  
  - Key edge cases and error scenarios are covered.  

### 6. **Documentation**
- Provide comprehensive documentation that includes:  
  - How to set up, run, and test the chatbot server.  
  - A clear description of the survey flow and state management approach.  
  - Assumptions made during the implementation.  
  - Design choices and their rationale.

---

## Optional Enhancements  

While the above requirements define the core functionality, adding optional features is highly encouraged to demonstrate creativity and engineering skills. Examples include:  

1. **Survey Enhancements**  
   - Dynamic surveys with questions loaded based on customer information (retrieved via RPC).  
   - Conditional branching based on previous answers.  

2. **Feedback Collection**  
   - Collect customer feedback about their experience with the chatbot.  

3. **Admin Controls**  
   - An interface for admins to view or manage collected survey responses (API-only).  
   - Ability to define or update surveys dynamically.  

4. **Advanced State Management**  
   - Implement mechanisms to store survey state in external storage (e.g., via RPC) for improved scalability.  

5. **WebSockets**  
   - Use websockets for client-server communication.

6. **Other Creative Features**  
   - Multi-language support for surveys.  
   - Real-time analytics or visualization of survey results (API endpoints only).

---

## Evaluation Criteria

Your submission will be evaluated on the following:

1. **Core Functionality**
   - Does the chatbot reliably guide customers through the survey?  
   - Are survey responses accurately collected and stored?  

2. **Code Quality**
   - Is the code modular, maintainable, and easy to understand?  
   - Are functions and modules appropriately named and concise?  

3. **Problem-Solving**
   - Does the solution demonstrate clear and logical problem-solving?  
   - Are design decisions well thought out and justified?  

4. **State Management**
   - Is the survey state handled effectively for multiple customers?  

5. **Error Handling**
   - Are errors managed gracefully, with meaningful fallbacks?  

6. **Real-Time Functionality**
   - Is WebSocket communication robust and reliable?  

7. **Documentation**
   - Is the documentation clear, complete, and easy to follow?  

8. **Optional Features**
   - Are optional features implemented in a way that adds meaningful value?  

9. **Preparedness for Live Discussion**
   - Are you able to explain and defend your implementation choices?  
   - Can you confidently make modifications during a live coding session?

---

## Submission Instructions  

1. Initialize the current directory (containing this README.md) as a Git repository.
2. Implement your solution.
3. Publish the repository in GitHub and provide us access, or, ZIP it and provide it to us via email attachment.
