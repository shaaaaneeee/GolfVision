from dataclasses import dataclass
import numpy as np

MIN_FRAMES = 20


@dataclass
class SwingPhases:
    """
    Swing phase boundaries. Tuple ranges are exclusive-end: (start, end)
    means frames start <= frame < end. p5_frame and p8_frame are exact
    frame indices for key events.
    """
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

    P5 (top of backswing): frame where LEFT_WRIST Y is at its minimum
    (excluding the first/last 10% of frames to avoid boundary artifacts).
    P8 (impact): frame of maximum absolute wrist velocity after P5.
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

    # Ensure P8 is strictly after P5 (minimum 1 frame gap)
    if p8_idx <= p5_idx:
        p8_idx = min(p5_idx + 1, len(frames) - 1)
    p8_frame = frames[p8_idx]

    # Address phase ends at frame 5 (or the margin, whichever is smaller).
    # This approximates the static setup frames before the swing starts.
    address_end_idx = min(5, margin)

    return SwingPhases(
        address=(frames[0], frames[address_end_idx]),
        backswing=(frames[address_end_idx], p5_frame),
        p5_frame=p5_frame,
        downswing=(p5_frame, p8_frame),
        p8_frame=p8_frame,
        follow_through=(p8_frame, frames[-1] + 1),
    )
