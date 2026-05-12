import pytest
from unittest.mock import patch, MagicMock
from api.worker import run_analysis


@pytest.fixture
def mock_landmarks(swing_sequence):
    return swing_sequence


def test_run_analysis_returns_expected_shape(mock_landmarks):
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


def test_run_analysis_faults_have_severity_floats(mock_landmarks):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Good feedback.")]
    )
    with patch("api.worker.extract_landmarks", return_value=mock_landmarks), \
         patch("api.worker.anthropic.Anthropic", return_value=mock_client):
        result = run_analysis("fake_path.mp4")

    for fault, severity in result["faults"].items():
        assert 0.0 <= severity <= 1.0


def test_run_analysis_includes_phase_frames(mock_landmarks):
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
