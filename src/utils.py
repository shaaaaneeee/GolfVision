"""
Utility helpers for Golf Vision.
"""

import json
import os


def load_pose_results(json_path: str) -> list:
    """Load AlphaPose JSON output into a list of frame results."""
    with open(json_path, 'r') as f:
        return json.load(f)


def get_keypoint(pose: dict, index: int) -> tuple:
    """Extract (x, y, confidence) for a keypoint by COCO index."""
    kps = pose.get('keypoints', [])
    if index * 3 + 2 >= len(kps):
        return None
    return kps[index * 3], kps[index * 3 + 1], kps[index * 3 + 2]


# COCO keypoint index reference
COCO_KEYPOINTS = {
    0: 'nose', 1: 'left_eye', 2: 'right_eye', 3: 'left_ear', 4: 'right_ear',
    5: 'left_shoulder', 6: 'right_shoulder', 7: 'left_elbow', 8: 'right_elbow',
    9: 'left_wrist', 10: 'right_wrist', 11: 'left_hip', 12: 'right_hip',
    13: 'left_knee', 14: 'right_knee', 15: 'left_ankle', 16: 'right_ankle',
}
