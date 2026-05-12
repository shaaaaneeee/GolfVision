from copy import deepcopy

VIS_THRESHOLD = 0.5


def smooth_landmarks(
    sequence: list[dict],
    alpha: float = 0.6,
) -> list[dict]:
    """
    Apply exponential smoothing to all landmark coordinates.
    Frames where a joint's visibility < VIS_THRESHOLD use the previous
    smoothed value instead of the raw value for that joint.
    """
    if not sequence:
        return []

    result = [deepcopy(sequence[0])]

    for frame in sequence[1:]:
        smoothed_frame = {}
        prev = result[-1]

        # First: carry forward any joints missing from the current frame
        for joint in prev:
            if joint not in frame:
                smoothed_frame[joint] = deepcopy(prev[joint])

        # Then: process joints present in current frame
        for joint, coords in frame.items():
            prev_coords = prev.get(joint, coords)
            if coords["vis"] < VIS_THRESHOLD:
                smoothed_frame[joint] = deepcopy(prev_coords)
                smoothed_frame[joint]["vis"] = coords["vis"]  # Fix 2: use current vis
            else:
                smoothed_frame[joint] = {
                    "x": alpha * coords["x"] + (1 - alpha) * prev_coords["x"],
                    "y": alpha * coords["y"] + (1 - alpha) * prev_coords["y"],
                    "z": alpha * coords["z"] + (1 - alpha) * prev_coords["z"],
                    "vis": coords["vis"],
                }
        result.append(smoothed_frame)

    return result
