# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Dict
from abc import ABC, abstractmethod
import uuid
from datetime import datetime

app = FastAPI(
    title="LLD Practice Platform Engine",
    description="A domain-driven MVP for practicing LLD trade-offs and iterative refactoring."
)

# ==========================================
# 1. DOMAIN ENUMS & DATA MODELS
# ==========================================

class AttemptState(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class CriterionScore(BaseModel):
    criterion_name: str
    score: int = Field(..., ge=1, le=5, description="Rubric score from 1 to 5")
    evidence: str
    concern: str
    suggestion: str

class FeedbackReport(BaseModel):
    id: str
    submission_id: str
    overall_score: int
    summary: str
    rubric_scores: List[CriterionScore]
    evaluated_at: str

class SubmissionPayload(BaseModel):
    design_rationale: str
    class_specification: str
    format_type: str = "HYBRID_TEXT_CODE"

class Attempt(BaseModel):
    id: str
    problem_id: str
    user_id: str
    version: int = 1
    parent_attempt_id: Optional[str] = None
    state: AttemptState
    submission: Optional[SubmissionPayload] = None
    feedback: Optional[FeedbackReport] = None
    created_at: str

# In-Memory Database Repositories
PROBLEMS_DB: Dict[str, dict] = {
    "prob_smart_bin": {
        "id": "prob_smart_bin",
        "title": "Smart Waste & Bin Management System",
        "description": "Design an LLD for an automated municipal smart bin collection network.",
        "requirements": [
            "SmartBins track fill levels (0-100%) and waste types (DRY, WET, HAZARDOUS).",
            "Auto-trigger collection alerts when bin capacity exceeds 80%.",
            "RouteOptimizationStrategy for collection trucks (Overflow priority vs Fuel efficient).",
            "Support bin maintenance states without breaking active truck routes."
        ],
        "starter_template": (
            "# Design Rationale\n"
            "1. Central WasteManagementService orchestrates collection.\n"
            "2. Strategy Pattern isolates routing algorithms.\n\n"
            "# Class Specification\n"
            "class SmartBin:\n"
            "    def __init__(self, bin_id: str, waste_type: str):\n"
            "        self.fill_level = 0.0\n"
        )
    }
}

ATTEMPTS_DB: Dict[str, Attempt] = {}

# ==========================================
# 2. EVALUATOR STRATEGY PATTERN
# ==========================================

class SubmissionEvaluator(ABC):
    @abstractmethod
    def evaluate(self, submission_id: str, payload: SubmissionPayload) -> FeedbackReport:
        pass

class DeterministicSanityChecker(SubmissionEvaluator):
    """Phase 1: Rule-based checker verifying structural payload completeness."""
    def evaluate(self, submission_id: str, payload: SubmissionPayload) -> FeedbackReport:
        scores = []
        if len(payload.class_specification.strip()) < 30:
            scores.append(CriterionScore(
                criterion_name="Structural Completeness",
                score=1,
                evidence=f"Code length is {len(payload.class_specification.strip())} chars.",
                concern="Class specification lacks sufficient class or interface declarations.",
                suggestion="Provide core entity definitions (e.g., SmartBin, RouteStrategy)."
            ))
        
        return FeedbackReport(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            overall_score=2 if scores else 5,
            summary="Deterministic validation check completed.",
            rubric_scores=scores,
            evaluated_at=datetime.now().isoformat()
        )

class LLMRubricEvaluator(SubmissionEvaluator):
    """Phase 2: Multi-dimensional AI rubric evaluation."""
    def evaluate(self, submission_id: str, payload: SubmissionPayload) -> FeedbackReport:
        rubric = [
            CriterionScore(
                criterion_name="Single Responsibility Principle (SRP)",
                score=4,
                evidence="SmartBin handles state updates while WasteManagementService handles routing.",
                concern="WasteManagementService directly handles alert notifications.",
                suggestion="Extract an AlertObserver interface to decouple notifications from routing."
            ),
            CriterionScore(
                criterion_name="Coupling & Abstraction",
                score=5,
                evidence="RouteStrategy interface used to isolate collection algorithms.",
                concern="None. Excellent application of the Strategy Pattern.",
                suggestion="Consider implementing an explicit State Pattern for BinState transitions."
            )
        ]
        return FeedbackReport(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            overall_score=88,
            summary="Solid domain encapsulation with clean entity boundaries.",
            rubric_scores=rubric,
            evaluated_at=datetime.now().isoformat()
        )

# ==========================================
# 3. BACKGROUND TASK ENGINE
# ==========================================

def run_async_evaluation(attempt_id: str):
    attempt = ATTEMPTS_DB.get(attempt_id)
    if not attempt or not attempt.submission:
        return

    attempt.state = AttemptState.EVALUATING
    
    try:
        # Phase 1: Deterministic Sanity Check
        sanity_checker = DeterministicSanityChecker()
        sanity_report = sanity_checker.evaluate(attempt_id, attempt.submission)
        
        if sanity_report.overall_score < 3:
            attempt.feedback = sanity_report
            attempt.state = AttemptState.COMPLETED
            return

        # Phase 2: Structured Rubric Evaluation
        ai_evaluator = LLMRubricEvaluator()
        final_report = ai_evaluator.evaluate(attempt_id, attempt.submission)
        
        attempt.feedback = final_report
        attempt.state = AttemptState.COMPLETED
    except Exception:
        attempt.state = AttemptState.FAILED

# ==========================================
# 4. REST API ENDPOINTS
# ==========================================

@app.get("/problems")
def list_problems():
    """1. Problem Selection: List all available LLD problems."""
    return list(PROBLEMS_DB.values())

@app.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    if problem_id not in PROBLEMS_DB:
        raise HTTPException(status_code=404, detail="Problem not found")
    return PROBLEMS_DB[problem_id]

@app.post("/attempts/start", response_model=Attempt)
def start_attempt(problem_id: str, user_id: str, parent_attempt_id: Optional[str] = None):
    """2. Practice Initialization: Start attempt #1 or a linked refactoring V2 attempt."""
    if problem_id not in PROBLEMS_DB:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    version = 1
    if parent_attempt_id:
        if parent_attempt_id not in ATTEMPTS_DB:
            raise HTTPException(status_code=404, detail="Parent attempt not found")
        version = ATTEMPTS_DB[parent_attempt_id].version + 1

    attempt = Attempt(
        id=str(uuid.uuid4()),
        problem_id=problem_id,
        user_id=user_id,
        version=version,
        parent_attempt_id=parent_attempt_id,
        state=AttemptState.DRAFT,
        created_at=datetime.now().isoformat()
    )
    ATTEMPTS_DB[attempt.id] = attempt
    return attempt

@app.post("/attempts/{attempt_id}/submit")
def submit_attempt(attempt_id: str, payload: SubmissionPayload, background_tasks: BackgroundTasks):
    """3. Submission: Accept solution draft and trigger async evaluation task."""
    attempt = ATTEMPTS_DB.get(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.state not in [AttemptState.DRAFT, AttemptState.FAILED]:
        raise HTTPException(status_code=400, detail="Attempt is already submitted or processing.")

    attempt.submission = payload
    attempt.state = AttemptState.SUBMITTED
    
    background_tasks.add_task(run_async_evaluation, attempt_id)
    
    return {
        "message": "Submission received successfully. Evaluation in progress.",
        "attempt_id": attempt_id,
        "state": attempt.state
    }

@app.get("/attempts/{attempt_id}", response_model=Attempt)
def get_attempt_status(attempt_id: str):
    """4. Feedback & Polling: Fetch attempt status and rubric feedback."""
    attempt = ATTEMPTS_DB.get(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt

@app.get("/users/{user_id}/history")
def get_user_history(user_id: str):
    """5. Attempt History: Track learner's refactoring progression across versions."""
    user_attempts = [att for att in ATTEMPTS_DB.values() if att.user_id == user_id]
    return sorted(user_attempts, key=lambda x: x.created_at, reverse=True)