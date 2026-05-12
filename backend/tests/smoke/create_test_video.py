"""Helper to create a minimal synthetic MP4 video for smoke testing."""

import cv2
import numpy as np


def create_test_video(output_path: str, num_frames: int = 30, fps: int = 30) -> None:
    """Create a synthetic MP4 for testing pose extraction."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (320, 240))
    for i in range(num_frames):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        # Add a simple stick figure outline so it's not completely empty
        cv2.circle(frame, (160, 60), 20, (200, 200, 200), 2)   # head
        cv2.line(frame, (160, 80), (160, 160), (200, 200, 200), 2)  # torso
        cv2.line(frame, (160, 100), (120, 140), (200, 200, 200), 2)  # left arm
        cv2.line(frame, (160, 100), (200, 140), (200, 200, 200), 2)  # right arm
        cv2.line(frame, (160, 160), (130, 220), (200, 200, 200), 2)  # left leg
        cv2.line(frame, (160, 160), (190, 220), (200, 200, 200), 2)  # right leg
        writer.write(frame)
    writer.release()
