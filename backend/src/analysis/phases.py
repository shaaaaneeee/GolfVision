from dataclasses import dataclass
import numpy as np

MIN_FRAMES = 20


@dataclass
class SwingPhases:
    address: tuple[int, int]
    backswing: tuple[int, int]
    p5_frame: int
    downswing: tuple[int, int]
    p8_frame: int
    follow_through: tuple[int, int]


def detect_phases(sequence: dict[int, dict]) -> SwingPhases:
    """
    Auto-detect P1–P10 swing phases from landmark sequence.
    Uses left wrist Y-coordinate velocity to locate key events.
    """
    if len(sequence) < MIN_FRAMES:
        raise ValueError(f"Sequence too short: {len(sequence)} frames (need {MIN_FRAMES})")

    frames = sorted(sequence.keys())
    wrist_y = np.array([sequence[f]["LEFT_WRIST"]["y"] for f in frames])
    wrist_vel = np.gradient(wrist_y)

    # P5: top of backswing = local minimum of wrist Y (exclude first/last 10%)
    margin = max(3, len(frames) // 10)
    search_region = wrist_y[margin:-margin]
    p5_idx = int(np.argmin(search_region)) + margin
    p5_frame = frames[p5_idx]

    # P8: impact = maximum absolute velocity after P5
    post_p5_vel = np.abs(wrist_vel[p5_idx:])
    p8_idx = int(np.argmax(post_p5_vel)) + p5_idx
    p8_frame = frames[p8_idx]

    return SwingPhases(
        address=(frames[0], frames[min(5, margin)]),
        backswing=(frames[min(5, margin)], p5_frame),
        p5_frame=p5_frame,
        downswing=(p5_frame, p8_frame),
        p8_frame=p8_frame,
        follow_through=(p8_frame, frames[-1] + 1),
    )
