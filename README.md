# LLD Practice Platform Engine (MVP Prototype)

An extensible, domain-driven Low-Level Design (LLD) practice engine built with FastAPI. It prioritizes the **learner refactoring loop** over generic LMS features by providing non-blocking execution, multi-dimensional rubric feedback, and immutable versioned submission tracking.

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
* Python 3.9+
* `pip` package manager

### 2. Environment Setup & Installation
```bash
# Clone or navigate into the project directory
cd "LLD Practice Platform"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate

# Install required dependencies (including httpx for TestClient)
pip install fastapi uvicorn pydantic pytest requests httpx

```

### 3. Run Automated Tests
Verify domain models, evaluation strategies, and state transitions:
```bash
cd python -m pytest test_domain.py -v
```

### 4. Start Local Development Server
Launch the live FastAPI application:
```bash
uvicorn main:app --reload
Interactive API Docs (Swagger UI): http://127.0.0.1:8000/docs
```

## How to Run & Verify the Learner Refactoring Loop
Follow this sequence in Swagger UI (http://127.0.0.1:8000/docs):

Browse Problems: Call GET /problems to inspect available scenarios (prob_smart_bin).

Start Attempt 1: Call POST /attempts/start with problem_id="prob_smart_bin" and user_id="user_sharath". Copy the generated id.

Submit Solution: Call POST /attempts/{attempt_id}/submit using the copied ID along with your rationale + code payload.

Fetch Feedback: Call GET /attempts/{attempt_id} to view your score breakdown (e.g., SRP, Coupling) once state moves to COMPLETED.

Start Version 2 (Refactoring): Call POST /attempts/start with parent_attempt_id="<attempt_1_id>" to establish a linked version: 2 attempt.

View Attempt History: Call GET /users/user_sharath/history to review your overall refactoring progression.

## Key Architecture Decisions
    Domain-Driven Core: Decoupled domain models (Attempt, Submission, FeedbackReport) from API infrastructure to ensure high testability and fast execution.

    Strategy Pattern Evaluators: Implemented an extensible EvaluationStrategy interface. Submissions route through a two-phase check:

        DeterministicSanityChecker: Instant rule-based validation (e.g., non-empty code, minimal structural lengths).

        LLMRubricEvaluator: Asynchronous multi-dimensional rubric scoring across explicit object-oriented metrics.

    State Machine Guards: Explicit attempt lifecycle states (DRAFT -> SUBMITTED -> PROCESSING -> COMPLETED / FAILED). Direct state transitions prevent double-submission race conditions.

    Non-Blocking Execution: Evaluation triggers asynchronously via FastAPI BackgroundTasks, releasing the learner HTTP thread instantly without forcing blocking wait times.

    Immutable Attempt Versioning: Iterations form an append-only linear tree via parent_attempt_id, maintaining full audit trails for tracking structural improvement over time.

## Limitations & Future Trade-Offs
In-Memory State: Data persistence relies on Python dictionaries (ATTEMPTS_DB, PROBLEMS_DB). Server restarts reset state; production requires PostgreSQL or DynamoDB.

Mocked LLM Infrastructure: The current LLMRubricEvaluator simulates multi-dimensional scoring deterministically to keep tests lightweight and offline-ready. Production requires real OpenAI/Groq API routing with fallback mechanisms.

Monolithic Background Processing: Uses internal background tasks instead of dedicated task queues. Production scaling would replace this with Celery/Redis or AWS SQS.

## AI Usage & Disclosure Log

### Overview & Purpose
AI tooling (LLMs) was leveraged during the development of this LLD Practice Platform MVP to assist with rapid prototyping, architectural refinement, unit test generation, and debugging setup issues.

Meaningful AI Contributions
1. Architecture & Design Partnering:

    Assisted in structuring the Strategy Pattern for multi-phase evaluation (DeterministicSanityChecker vs. LLMRubricEvaluator).

    Refined the versioned state machine logic to handle non-blocking transitions safely.

2. Test Suite Generation:

    Generated initial test coverage for domain rules, state guard assertions, and edge-case handling in test_domain.py.

3. Troubleshooting & Debugging:

    Identified and provided resolutions for environment issues during setup (such as missing httpx dependencies for fastapi.testclient and path formatting for Windows PowerShell).

