import pytest
from analysis.phases import detect_phases, SwingPhases


def test_detects_p5_near_minimum_wrist_y(swing_sequence):
    phases = detect_phases(swing_sequence)
    # In fixture, wrist y minimum is frame 14 (top of backswing)
    assert abs(phases.p5_frame - 14) <= 2


def test_detects_p8_after_p5(swing_sequence):
    phases = detect_phases(swing_sequence)
    assert phases.p8_frame > phases.p5_frame


def test_phase_labels_cover_all_frames(swing_sequence):
    phases = detect_phases(swing_sequence)
    assert phases.p5_frame < phases.p8_frame
    assert phases.address[0] < phases.address[1]
    assert phases.backswing[0] < phases.backswing[1]
    assert phases.downswing[0] < phases.downswing[1]


def test_raises_on_too_short_sequence():
    tiny = {i: {"LEFT_WRIST": {"x": 0.5, "y": 0.5, "z": 0.0, "vis": 1.0}} for i in range(5)}
    with pytest.raises(ValueError, match="too short"):
        detect_phases(tiny)


def test_follow_through_end_is_exclusive(swing_sequence):
    """follow_through tuple end should be one past the last frame (exclusive-end)."""
    phases = detect_phases(swing_sequence)
    last_frame = max(swing_sequence.keys())
    assert phases.follow_through[1] == last_frame + 1
