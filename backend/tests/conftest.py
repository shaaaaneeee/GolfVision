from copy import deepcopy
import pytest


def _frame(lh_x, lh_y, rh_x, rh_y, ls_x, ls_y, rs_x, rs_y,
           lw_x=0.5, lw_y=0.5, vis=1.0) -> dict:
    return {
        "LEFT_HIP":      {"x": lh_x, "y": lh_y,  "z": 0.0, "vis": vis},
        "RIGHT_HIP":     {"x": rh_x, "y": rh_y,  "z": 0.0, "vis": vis},
        "LEFT_SHOULDER": {"x": ls_x, "y": ls_y,  "z": 0.0, "vis": vis},
        "RIGHT_SHOULDER":{"x": rs_x, "y": rs_y,  "z": 0.0, "vis": vis},
        "LEFT_WRIST":    {"x": lw_x, "y": lw_y,  "z": 0.0, "vis": vis},
        "RIGHT_WRIST":   {"x": 0.6,  "y": 0.5,   "z": 0.0, "vis": vis},
        "LEFT_ELBOW":    {"x": 0.4,  "y": 0.45,  "z": 0.0, "vis": vis},
        "RIGHT_ELBOW":   {"x": 0.6,  "y": 0.45,  "z": 0.0, "vis": vis},
        "LEFT_KNEE":     {"x": 0.45, "y": 0.7,   "z": 0.0, "vis": vis},
        "RIGHT_KNEE":    {"x": 0.55, "y": 0.7,   "z": 0.0, "vis": vis},
        "LEFT_ANKLE":    {"x": 0.45, "y": 0.9,   "z": 0.0, "vis": vis},
        "RIGHT_ANKLE":   {"x": 0.55, "y": 0.9,   "z": 0.0, "vis": vis},
        "NOSE":          {"x": 0.5,  "y": 0.05,  "z": 0.0, "vis": vis},
        "LEFT_EAR":      {"x": 0.45, "y": 0.07,  "z": 0.0, "vis": vis},
    }


@pytest.fixture
def address_frame():
    return _frame(
        lh_x=0.45, lh_y=0.55, rh_x=0.55, rh_y=0.55,
        ls_x=0.44, ls_y=0.35, rs_x=0.56, rs_y=0.35,
        lw_x=0.5,  lw_y=0.65,
    )


@pytest.fixture
def top_of_backswing_frame():
    """P5 frame: shoulder axis ~27 deg ahead of hip axis (realistic X-factor)."""
    return _frame(
        lh_x=0.44, lh_y=0.55, rh_x=0.56, rh_y=0.55,  # hip axis ~0 deg
        ls_x=0.20, ls_y=0.45, rs_x=0.70, rs_y=0.20,   # shoulder axis ~-27 deg
        lw_x=0.3,  lw_y=0.2,
    )


@pytest.fixture
def swing_sequence(address_frame, top_of_backswing_frame):
    """Synthetic 30-frame golf swing: address (0-4), backswing (5-14), downswing (15-24), follow-through (25-29)."""
    frames = {}
    for i in range(5):
        f = deepcopy(address_frame)
        f["LEFT_WRIST"] = {"x": 0.5, "y": 0.65, "z": 0.0, "vis": 1.0}
        frames[i] = f

    for i in range(5, 15):
        t = (i - 5) / 9.0
        wrist_y = 0.65 - t * 0.45
        f = deepcopy(top_of_backswing_frame)
        f["LEFT_WRIST"] = {"x": 0.5 - t * 0.2, "y": wrist_y, "z": 0.0, "vis": 1.0}
        frames[i] = f

    for i in range(15, 25):
        t = (i - 15) / 9.0
        wrist_y = 0.20 + t * 0.50
        f = deepcopy(address_frame)
        f["LEFT_WRIST"] = {"x": 0.3 + t * 0.2, "y": wrist_y, "z": 0.0, "vis": 1.0}
        frames[i] = f

    for i in range(25, 30):
        f = deepcopy(address_frame)
        f["LEFT_WRIST"] = {"x": 0.7, "y": 0.3, "z": 0.0, "vis": 1.0}
        frames[i] = f

    return frames
