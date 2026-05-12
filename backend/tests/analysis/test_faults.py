import pytest
from analysis.faults import detect_faults, FAULT_THRESHOLDS


def test_detects_insufficient_xfactor():
    features = {"hip_shoulder_sep_at_p5": 20.0, "hip_forward_shift_p6_p8": 0.02, "weight_trail_at_p5": 0.60}
    faults = detect_faults(features)
    assert faults["insufficient_x_factor"] == pytest.approx(0.429, abs=0.001)


def test_no_fault_when_xfactor_good():
    features = {"hip_shoulder_sep_at_p5": 45.0, "hip_forward_shift_p6_p8": 0.02, "weight_trail_at_p5": 0.60}
    faults = detect_faults(features)
    assert faults["insufficient_x_factor"] == 0.0


def test_detects_early_extension():
    features = {"hip_shoulder_sep_at_p5": 40.0, "hip_forward_shift_p6_p8": 0.12, "weight_trail_at_p5": 0.60}
    faults = detect_faults(features)
    assert faults["early_extension"] == pytest.approx(0.7, abs=0.001)


def test_detects_reverse_pivot():
    features = {"hip_shoulder_sep_at_p5": 40.0, "hip_forward_shift_p6_p8": 0.02, "weight_trail_at_p5": 0.30}
    faults = detect_faults(features)
    assert faults["reverse_pivot"] == pytest.approx(0.455, abs=0.001)


def test_severity_clipped_to_one():
    features = {"hip_shoulder_sep_at_p5": 0.0, "hip_forward_shift_p6_p8": 0.02, "weight_trail_at_p5": 0.60}
    faults = detect_faults(features)
    assert faults["insufficient_x_factor"] == pytest.approx(1.0)


def test_returns_all_fault_keys():
    features = {"hip_shoulder_sep_at_p5": 40.0, "hip_forward_shift_p6_p8": 0.02, "weight_trail_at_p5": 0.60}
    faults = detect_faults(features)
    for fault in FAULT_THRESHOLDS:
        assert fault in faults


def test_missing_feature_returns_zero_severity():
    faults = detect_faults({})  # empty feature dict
    for fault in FAULT_THRESHOLDS:
        assert faults[fault] == 0.0
