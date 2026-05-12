import numpy as np
from analysis.phases import SwingPhases


def compute_angle(a: list, b: list, c: list) -> float:
    """Angle in degrees at joint b, formed by points a-b-c."""
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def hip_shoulder_separation(frame: dict) -> float:
    """
    X-factor: angular separation between hips and shoulders in degrees.
    Measured as the difference between the angle from each hip joint to its
    corresponding shoulder joint (left hip->left shoulder vs right hip->right
    shoulder). Higher = more rotation separation = more stored power.
    """
    lh, rh = frame["LEFT_HIP"], frame["RIGHT_HIP"]
    ls, rs = frame["LEFT_SHOULDER"], frame["RIGHT_SHOULDER"]
    left_ang  = np.degrees(np.arctan2(ls["y"] - lh["y"], ls["x"] - lh["x"]))
    right_ang = np.degrees(np.arctan2(rs["y"] - rh["y"], rs["x"] - rh["x"]))
    return float(abs(left_ang - right_ang))


def lateral_hip_shift(frame_early: dict, frame_late: dict) -> float:
    """
    Change in hip midpoint X position between two frames.
    Positive = moved toward target (left for right-handed golfer).
    """
    mx_early = (frame_early["LEFT_HIP"]["x"] + frame_early["RIGHT_HIP"]["x"]) / 2
    mx_late  = (frame_late["LEFT_HIP"]["x"]  + frame_late["RIGHT_HIP"]["x"])  / 2
    return float(mx_late - mx_early)


def _weight_trail_ratio(frame: dict) -> float:
    """
    Estimate trail-side weight ratio from hip midpoint position relative
    to ankle midpoints. Returns 0.0–1.0 (1.0 = fully on trail side).
    """
    hip_x   = (frame["LEFT_HIP"]["x"]   + frame["RIGHT_HIP"]["x"])   / 2
    trail_x = frame["RIGHT_ANKLE"]["x"]
    lead_x  = frame["LEFT_ANKLE"]["x"]
    width = abs(trail_x - lead_x) + 1e-6
    return float(np.clip((trail_x - hip_x) / width, 0.0, 1.0))


def compute_swing_features(
    sequence: dict[int, dict],
    phases: SwingPhases,
) -> dict[str, float]:
    """
    Compute the core biomechanical feature vector for a full swing.
    Returns {feature_name: float}.
    """
    def nearest_frame(target: int) -> dict:
        key = min(sequence.keys(), key=lambda k: abs(k - target))
        return sequence[key]

    p5_frame = nearest_frame(phases.p5_frame)
    p8_frame = nearest_frame(phases.p8_frame)
    p6_frame = nearest_frame(phases.p5_frame + 1)

    features: dict[str, float] = {}
    features["hip_shoulder_sep_at_p5"] = hip_shoulder_separation(p5_frame)
    features["hip_forward_shift_p6_p8"] = lateral_hip_shift(p6_frame, p8_frame)
    features["weight_trail_at_p5"] = _weight_trail_ratio(p5_frame)

    return features
