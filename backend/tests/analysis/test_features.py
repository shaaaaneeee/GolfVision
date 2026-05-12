import numpy as np
import pytest
from analysis.features import (
    compute_angle,
    hip_shoulder_separation,
    lateral_hip_shift,
    compute_swing_features,
)


def test_compute_angle_right_angle():
    a = [1.0, 0.0]
    b = [0.0, 0.0]
    c = [0.0, 1.0]
    assert compute_angle(a, b, c) == pytest.approx(90.0, abs=0.1)


def test_compute_angle_straight_line():
    a = [0.0, 0.0]
    b = [1.0, 0.0]
    c = [2.0, 0.0]
    assert compute_angle(a, b, c) == pytest.approx(180.0, abs=0.1)


def test_hip_shoulder_separation_high_xfactor(top_of_backswing_frame):
    sep = hip_shoulder_separation(top_of_backswing_frame)
    assert sep > 20.0


def test_hip_shoulder_separation_low_at_address(address_frame):
    sep = hip_shoulder_separation(address_frame)
    assert sep < 10.0


def test_lateral_hip_shift_detects_forward_movement():
    frame_early = {"LEFT_HIP": {"x": 0.45, "y": 0.5, "z": 0.0, "vis": 1.0},
                   "RIGHT_HIP": {"x": 0.55, "y": 0.5, "z": 0.0, "vis": 1.0}}
    frame_late  = {"LEFT_HIP": {"x": 0.50, "y": 0.5, "z": 0.0, "vis": 1.0},
                   "RIGHT_HIP": {"x": 0.60, "y": 0.5, "z": 0.0, "vis": 1.0}}
    shift = lateral_hip_shift(frame_early, frame_late)
    assert shift > 0.0


def test_compute_swing_features_returns_all_keys(swing_sequence, address_frame,
                                                  top_of_backswing_frame):
    from analysis.phases import detect_phases
    phases = detect_phases(swing_sequence)
    features = compute_swing_features(swing_sequence, phases)
    expected_keys = {
        "hip_shoulder_sep_at_p5",
        "hip_forward_shift_p6_p8",
        "weight_trail_at_p5",
    }
    for k in expected_keys:
        assert k in features
        assert isinstance(features[k], float)
