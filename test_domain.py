# test_domain.py
import pytest
from fastapi.testclient import TestClient
from main import app, ATTEMPTS_DB, DeterministicSanityChecker, SubmissionPayload

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    """Clear memory database state before each test execution."""
    ATTEMPTS_DB.clear()

def test_complete_e2e_learner_flow():
    """Test 1: Full flow from problem selection to feedback and history."""
    resp = client.get("/problems")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    prob_id = resp.json()[0]["id"]

    start_resp = client.post(f"/attempts/start?problem_id={prob_id}&user_id=user_sharath")
    assert start_resp.status_code == 200
    attempt_id = start_resp.json()["id"]
    assert start_resp.json()["version"] == 1
    assert start_resp.json()["state"] == "DRAFT"

    payload = {
        "design_rationale": "Used Strategy Pattern for routing algorithms.",
        "class_specification": "class SmartBin:\n    def __init__(self): self.fill = 0\n\nclass RouteStrategy:\n    def optimize(self): pass"
    }
    sub_resp = client.post(f"/attempts/{attempt_id}/submit", json=payload)
    assert sub_resp.status_code == 200
    assert sub_resp.json()["state"] == "SUBMITTED"

    get_resp = client.get(f"/attempts/{attempt_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["state"] == "COMPLETED"
    assert data["feedback"]["overall_score"] == 88
    assert len(data["feedback"]["rubric_scores"]) == 2

    v2_resp = client.post(f"/attempts/start?problem_id={prob_id}&user_id=user_sharath&parent_attempt_id={attempt_id}")
    assert v2_resp.status_code == 200
    assert v2_resp.json()["version"] == 2
    assert v2_resp.json()["parent_attempt_id"] == attempt_id

    hist_resp = client.get("/users/user_sharath/history")
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) == 2

def test_sanity_checker_triggers_failure_for_short_code():
    """Test 2: Deterministic evaluator flags inadequate class specifications."""
    checker = DeterministicSanityChecker()
    payload = SubmissionPayload(
        design_rationale="Minimal rationale",
        class_specification="class A: pass"
    )
    report = checker.evaluate("sub_123", payload)
    assert report.overall_score == 2
    assert report.rubric_scores[0].criterion_name == "Structural Completeness"

def test_prevent_double_submission_edge_case():
    """Test 3: Double submission guard returns HTTP 400."""
    start_resp = client.post("/attempts/start?problem_id=prob_smart_bin&user_id=user_1")
    attempt_id = start_resp.json()["id"]

    payload = {"design_rationale": "Test", "class_specification": "class SmartBin: pass\nclass Route: pass"}
    client.post(f"/attempts/{attempt_id}/submit", json=payload)

    second_sub = client.post(f"/attempts/{attempt_id}/submit", json=payload)
    assert second_sub.status_code == 400
    assert "already submitted or processing" in second_sub.json()["detail"]

def test_start_attempt_invalid_parent_id():
    """Test 4: Invalid parent_attempt_id returns HTTP 404."""
    resp = client.post("/attempts/start?problem_id=prob_smart_bin&user_id=user_1&parent_attempt_id=invalid_id")
    assert resp.status_code == 404
    assert "Parent attempt not found" in resp.json()["detail"]