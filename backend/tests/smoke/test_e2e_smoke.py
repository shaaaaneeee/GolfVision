"""
End-to-end smoke test for the GolfVision backend pipeline.

To run against a real golf swing video:
    ANTHROPIC_API_KEY=<key> python -m pytest tests/smoke/ -v --no-header

To run with synthetic video (no API key needed):
    python -m pytest tests/smoke/ -v --no-header
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest

from tests.smoke.create_test_video import create_test_video
from pose.extractor import extract_landmarks
from pose.smoother import smooth_landmarks
from analysis.phases import SwingPhases, detect_phases
from analysis.features import compute_swing_features
from analysis.faults import detect_faults
from feedback.coach import generate_coaching


def make_mock_client():
    """Return a mock Anthropic client that returns a canned coaching response."""
    mock_content = MagicMock()
    mock_content.text = "Focus on maintaining your hip-shoulder separation through impact."
    mock_message = MagicMock()
    mock_message.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message
    return mock_client


@pytest.mark.smoke
def test_full_pipeline_with_synthetic_video():
    """
    Smoke test: creates a synthetic video, runs pose extraction, then the full
    analysis pipeline. Skips gracefully if MediaPipe cannot detect a person in
    the synthetic frames (acceptable in CI without a real golf video).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_swing.mp4")
        create_test_video(video_path, num_frames=30, fps=30)

        assert os.path.exists(video_path), "Synthetic video file was not created"
        assert os.path.getsize(video_path) > 0, "Synthetic video file is empty"

        # --- Pose extraction ---
        raw_sequence = extract_landmarks(video_path)

        if not raw_sequence:
            pytest.skip(
                "No landmarks detected in synthetic video — "
                "MediaPipe requires a real person. "
                "Run with a real golf swing video for full pipeline validation."
            )

        # --- Smoothing ---
        sorted_keys = sorted(raw_sequence.keys())
        sequence_list = [raw_sequence[k] for k in sorted_keys]
        smoothed_list = smooth_landmarks(sequence_list, alpha=0.6)
        assert len(smoothed_list) == len(sorted_keys), (
            "Smoother output length should match input length"
        )
        smoothed = {sorted_keys[i]: f for i, f in enumerate(smoothed_list)}

        # --- Phase detection ---
        phases = detect_phases(smoothed)
        assert isinstance(phases, SwingPhases), "detect_phases must return a SwingPhases"
        assert hasattr(phases, "p5_frame"), "SwingPhases must have p5_frame attribute"
        assert hasattr(phases, "p8_frame"), "SwingPhases must have p8_frame attribute"
        assert phases.p5_frame in sorted_keys, (
            f"p5_frame {phases.p5_frame} not in valid frame indices"
        )
        assert phases.p8_frame in sorted_keys, (
            f"p8_frame {phases.p8_frame} not in valid frame indices"
        )
        assert phases.p8_frame > phases.p5_frame, (
            "p8_frame (impact) must be after p5_frame (top of backswing)"
        )

        # --- Feature computation ---
        features = compute_swing_features(smoothed, phases)
        assert isinstance(features, dict), "compute_swing_features must return a dict"
        expected_feature_keys = {
            "hip_shoulder_sep_at_p5",
            "hip_forward_shift_p6_p8",
            "weight_trail_at_p5",
        }
        assert set(features.keys()) == expected_feature_keys, (
            f"Expected feature keys {expected_feature_keys}, got {set(features.keys())}"
        )
        for key, val in features.items():
            assert isinstance(val, float), f"Feature {key!r} must be a float, got {type(val)}"

        # --- Fault detection ---
        faults = detect_faults(features)
        assert isinstance(faults, dict), "detect_faults must return a dict"
        for fault_name, severity in faults.items():
            assert isinstance(fault_name, str), "Fault keys must be strings"
            assert isinstance(severity, float), (
                f"Fault severity for {fault_name!r} must be a float"
            )
            assert 0.0 <= severity <= 1.0, (
                f"Fault severity for {fault_name!r} must be in [0, 1], got {severity}"
            )

        # --- Coaching (mock client — no real API call) ---
        mock_client = make_mock_client()
        coaching = generate_coaching(faults, skill_level="intermediate", client=mock_client)
        assert isinstance(coaching, str), "generate_coaching must return a string"
        assert len(coaching) > 0, "Coaching response must not be empty"
