from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app, _jobs

client = TestClient(app)


def test_analyze_returns_job_id():
    with patch("api.main._process_job"):  # prevent background thread from running
        response = client.post(
            "/analyze",
            files={"video": ("swing.mp4", b"fake-video-bytes", "video/mp4")},
            data={"skill_level": "intermediate"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert isinstance(data["job_id"], str)
    assert len(data["job_id"]) > 0


def test_result_processing_returns_status():
    _jobs["proc-job"] = {"status": "processing"}
    response = client.get("/result/proc-job")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"


def test_result_complete_returns_faults():
    _jobs["done-job"] = {
        "status": "complete",
        "faults": {"early_extension": 0.7, "reverse_pivot": 0.0},
        "coaching": "Focus on hip separation.",
        "features": {"hip_shoulder_sep_at_p5": 32.0},
    }
    response = client.get("/result/done-job")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"
    assert data["coaching"] == "Focus on hip separation."
    assert isinstance(data["faults"], list)
    assert len(data["faults"]) > 0


def test_result_not_found_returns_404():
    response = client.get("/result/nonexistent-job-id")
    assert response.status_code == 404


def test_result_failed_returns_error():
    _jobs["fail-job"] = {"status": "failed", "error": "Analysis failed. Please try again."}
    response = client.get("/result/fail-job")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error"] is not None


def test_analyze_rejects_oversized_file():
    response = client.post(
        "/analyze",
        files={"video": ("big.mp4", b"x" * (51 * 1024 * 1024), "video/mp4")},
        data={"skill_level": "intermediate"},
    )
    assert response.status_code == 413
