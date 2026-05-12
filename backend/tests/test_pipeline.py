import os
import pytest
from unittest.mock import patch, MagicMock
from api.worker import run_analysis


@pytest.fixture
def mock_landmarks(swing_sequence):
    return swing_sequence


def test_run_analysis_returns_expected_shape(mock_landmarks, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Focus on hip separation.")]
    )
    with patch("api.worker.extract_landmarks", return_value=mock_landmarks), \
         patch("api.worker.anthropic.Anthropic", return_value=mock_client):
        result = run_analysis("fake_path.mp4", skill_level="intermediate")
    assert "faults" in result
    assert "coaching" in result
    assert "features" in result
    assert isinstance(result["faults"], dict)
    assert isinstance(result["coaching"], str)


def test_run_analysis_faults_have_severity_floats(mock_landmarks, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Good feedback.")]
    )
    with patch("api.worker.extract_landmarks", return_value=mock_landmarks), \
         patch("api.worker.anthropic.Anthropic", return_value=mock_client):
        result = run_analysis("fake_path.mp4")
    for fault, severity in result["faults"].items():
        assert 0.0 <= severity <= 1.0


def test_run_analysis_includes_phase_frames(mock_landmarks, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Good feedback.")]
    )
    with patch("api.worker.extract_landmarks", return_value=mock_landmarks), \
         patch("api.worker.anthropic.Anthropic", return_value=mock_client):
        result = run_analysis("fake_path.mp4")
    assert "phases" in result
    assert "p5_frame" in result["phases"]
    assert "p8_frame" in result["phases"]


def test_run_analysis_empty_video_returns_error():
    """Empty landmark sequence returns error dict, does not raise."""
    with patch("api.worker.extract_landmarks", return_value={}):
        result = run_analysis("empty_video.mp4")
    assert "error" in result
    assert result["faults"] == {}
    assert result["coaching"] != ""


def test_run_analysis_raises_on_missing_api_key(monkeypatch):
    """Missing ANTHROPIC_API_KEY raises ValueError."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    mock_landmarks_data = {i: {} for i in range(30)}  # placeholder
    with patch("api.worker.extract_landmarks", return_value=mock_landmarks_data), \
         patch("api.worker.detect_phases", return_value=MagicMock(p5_frame=14, p8_frame=24)), \
         patch("api.worker.compute_swing_features", return_value={}), \
         patch("api.worker.detect_faults", return_value={}):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            run_analysis("fake.mp4")
