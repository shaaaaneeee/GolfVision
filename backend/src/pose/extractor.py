import json
from pathlib import Path
import cv2
import mediapipe as mp

_mp_pose = mp.solutions.pose

JOINT_NAMES: list[str] = [p.name for p in _mp_pose.PoseLandmark]


def parse_world_landmarks(results) -> dict | None:
    """Convert a MediaPipe results object into a {joint_name: {x,y,z,vis}} dict."""
    if results.pose_world_landmarks is None:
        return None
    lm = results.pose_world_landmarks.landmark
    return {
        _mp_pose.PoseLandmark(i).name: {
            "x": l.x,
            "y": l.y,
            "z": l.z,
            "vis": l.visibility,
        }
        for i, l in enumerate(lm)
    }


def extract_landmarks(video_path: str) -> dict[int, dict]:
    """
    Process a video file and return per-frame landmark data.
    Returns {frame_index: {joint_name: {x, y, z, vis}}}.
    Frames where MediaPipe has no detection are omitted.
    """
    cap = cv2.VideoCapture(video_path)
    landmarks_data: dict[int, dict] = {}
    frame_idx = 0

    with _mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=2,
    ) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)
            parsed = parse_world_landmarks(results)
            if parsed is not None:
                landmarks_data[frame_idx] = parsed
            frame_idx += 1

    cap.release()
    return landmarks_data


def save_landmarks(landmarks: dict[int, dict], output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({str(k): v for k, v in landmarks.items()}, f)


def load_landmarks(path: str) -> dict[int, dict]:
    with open(path) as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}
