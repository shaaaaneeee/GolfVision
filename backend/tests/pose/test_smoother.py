import numpy as np
import pytest
from pose.smoother import smooth_landmarks

def make_seq(values: list[float]) -> list[dict]:
    """Build minimal landmark sequence with a single joint for testing."""
    return [{"NOSE": {"x": v, "y": 0.0, "z": 0.0, "vis": 1.0}} for v in values]

def test_smoother_reduces_variance():
    noisy = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    seq = make_seq(noisy)
    result = smooth_landmarks(seq, alpha=0.6)
    raw_var = float(np.var(noisy))
    smoothed_x = [f["NOSE"]["x"] for f in result]
    smooth_var = float(np.var(smoothed_x))
    assert smooth_var < raw_var

def test_smoother_preserves_frame_count():
    seq = make_seq([0.1, 0.2, 0.3, 0.4])
    result = smooth_landmarks(seq, alpha=0.6)
    assert len(result) == 4

def test_smoother_first_frame_unchanged():
    seq = make_seq([0.5, 0.9, 0.1])
    result = smooth_landmarks(seq, alpha=0.6)
    assert result[0]["NOSE"]["x"] == pytest.approx(0.5)

def test_smoother_rejects_low_visibility_coords():
    """Frames with vis < 0.5 on a joint should keep the previous smoothed value."""
    seq = [
        {"NOSE": {"x": 0.5, "y": 0.0, "z": 0.0, "vis": 1.0}},
        {"NOSE": {"x": 99.0, "y": 0.0, "z": 0.0, "vis": 0.1}},  # low vis
        {"NOSE": {"x": 0.5, "y": 0.0, "z": 0.0, "vis": 1.0}},
    ]
    result = smooth_landmarks(seq, alpha=0.6)
    # frame 1 low-vis spike should not propagate far
    assert result[1]["NOSE"]["x"] < 10.0

def test_smoother_propagates_missing_joints():
    """Joints missing from a frame should be carried forward from the previous frame."""
    seq = [
        {"NOSE": {"x": 0.5, "y": 0.3, "z": 0.0, "vis": 1.0}, "EYE": {"x": 0.4, "y": 0.2, "z": 0.0, "vis": 1.0}},
        {"NOSE": {"x": 0.6, "y": 0.3, "z": 0.0, "vis": 1.0}},  # EYE missing
        {"NOSE": {"x": 0.7, "y": 0.3, "z": 0.0, "vis": 1.0}},  # EYE still missing
    ]
    result = smooth_landmarks(seq, alpha=0.6)
    assert "EYE" in result[1], "EYE should be carried forward to frame 1"
    assert "EYE" in result[2], "EYE should be carried forward to frame 2"
    assert result[1]["EYE"]["x"] == pytest.approx(0.4)  # frozen from frame 0
