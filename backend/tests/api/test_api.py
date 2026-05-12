import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True, scope="module")
def mock_redis_connection():
    with patch("redis.from_url", return_value=MagicMock()):
        yield


def get_client():
    from api.main import app
    return TestClient(app)


def test_analyze_returns_job_id():
    client = get_client()
    mock_queue = MagicMock()
    mock_job = MagicMock()
    mock_job.id = "test-job-123"
    mock_queue.enqueue.return_value = mock_job

    with patch("api.main._queue", mock_queue):
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
    client = get_client()
    mock_job = MagicMock()
    mock_job.is_finished = False
    mock_job.is_failed = False

    with patch("api.main.Job") as MockJob:
        MockJob.fetch.return_value = mock_job
        response = client.get("/result/some-job-id")

    assert response.status_code == 200
    assert response.json()["status"] in ("queued", "processing")


def test_result_complete_returns_faults():
    client = get_client()
    mock_job = MagicMock()
    mock_job.is_finished = True
    mock_job.is_failed = False
    mock_job.result = {
        "faults": {"early_extension": 0.7, "reverse_pivot": 0.0},
        "coaching": "Focus on hip separation.",
        "features": {"hip_shoulder_sep_at_p5": 32.0},
        "phases": {"p5_frame": 14, "p8_frame": 20},
    }

    with patch("api.main.Job") as MockJob:
        MockJob.fetch.return_value = mock_job
        response = client.get("/result/finished-job-id")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"
    assert data["coaching"] == "Focus on hip separation."
    assert isinstance(data["faults"], list)
    assert len(data["faults"]) > 0


def test_result_not_found_returns_404():
    client = get_client()
    from rq.exceptions import NoSuchJobError

    with patch("api.main.Job") as MockJob:
        MockJob.fetch.side_effect = NoSuchJobError("not found")
        response = client.get("/result/nonexistent-job-id")

    assert response.status_code == 404


def test_result_failed_returns_error():
    client = get_client()
    mock_job = MagicMock()
    mock_job.is_finished = False
    mock_job.is_failed = True
    mock_job.exc_info = "Connection timeout: worker crash"

    with patch("api.main.Job") as MockJob:
        MockJob.fetch.return_value = mock_job
        response = client.get("/result/failed-job-id")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error"] is not None


def test_analyze_rejects_oversized_file():
    client = get_client()
    # Create a fake file larger than 50MB
    large_content = b"x" * (51 * 1024 * 1024)

    response = client.post(
        "/analyze",
        files={"video": ("big.mp4", large_content, "video/mp4")},
        data={"skill_level": "intermediate"},
    )

    assert response.status_code == 413
