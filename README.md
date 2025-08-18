# Campus Helpdesk

This repository contains the source code for the Campus Helpdesk, a microservices-based application designed to assist students with common issues and requests.

## Architecture

The system is built on a microservices architecture, with the following key components:

-   **Gateway**: The main entry point for all requests. It orchestrates the flow between the other services.
-   **Router**: Determines the user's intent based on their query.
-   **Policy**: Checks for relevant policies and returns citations.
-   **Answer**: Composes a response to the user's query.
-   **Action**: Executes actions on behalf of the user (e.g., resetting a password).
-   **Ticket**: Manages helpdesk tickets.
-   **Escalation**: Summarizes tickets for human operators.
-   **Ingest**: Handles incoming messages from various channels (e.g., Zalo).

## Getting Started

### Prerequisites

-   Docker and Docker Compose
-   Python 3.11+
-   An `.env` file (you can copy `.env.example` to get started)

### Installation and Running

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/campus-helpdesk.git
    cd campus-helpdesk
    ```

2.  **Set up the environment:**
    Copy the `.env.example` file to `.env` and fill in the required values.
    ```bash
    cp .env.example .env
    ```

3.  **Build and run the services:**
    ```bash
    docker-compose up --build -d
    ```
    The services will be available at their respective ports, as defined in `docker-compose.yml`.

## API Endpoints

### Gateway

-   `POST /ask`: The main endpoint for asking questions.
    -   Query parameter: `use_llm` (boolean, optional): Whether to use the LLM-based services.
    -   Request body:
        ```json
        {
            "channel": "web",
            "text": "How do I reset my password?",
            "student_id": "12345"
        }
        ```
    -   Example with `curl`:
        ```bash
        curl -X POST "http://localhost:8000/ask?use_llm=true" -H "Content-Type: application/json" -d '{
            "channel": "web",
            "text": "làm thế nào để đặt lại mật khẩu của tôi?",
            "student_id": "12345"
        }'
        ```

### Policy Service

-   `POST /ingest_policies`: Ingests policy documents into the vector store.
-   `POST /rag_answer`: (Experimental) Returns a RAG-based answer.

## LLM Integration

The system can be configured to use a Large Language Model (LLM) for intent classification and response composition. To enable this, set the `LLM_PROVIDER` environment variable to one of the following values:

-   `openai`
-   `vllm`
-   `ollama`

If `LLM_PROVIDER` is not set, the system will fall back to a rule-based stub.

## Testing

To run the tests, you will need to install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Then, you can run the tests with `pytest`:

```bash
pytest -q
```
