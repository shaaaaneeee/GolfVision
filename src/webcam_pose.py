"""
Golf Vision — Live Webcam Pose Estimation
Uses MediaPipe Tasks API. Draws skeleton manually via OpenCV.
Press Q to quit.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import os

from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'pose_landmarker_full.task')

# Landmark indices
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_ELBOW,    RIGHT_ELBOW    = 13, 14
LEFT_WRIST,    RIGHT_WRIST    = 15, 16
LEFT_HIP,      RIGHT_HIP      = 23, 24
LEFT_KNEE,     RIGHT_KNEE     = 25, 26
LEFT_ANKLE,    RIGHT_ANKLE    = 27, 28

CONNECTIONS = [
    # Torso
    (LEFT_SHOULDER, RIGHT_SHOULDER),
    (LEFT_SHOULDER, LEFT_HIP),
    (RIGHT_SHOULDER, RIGHT_HIP),
    (LEFT_HIP, RIGHT_HIP),
    # Left arm
    (LEFT_SHOULDER, LEFT_ELBOW),
    (LEFT_ELBOW, LEFT_WRIST),
    # Right arm
    (RIGHT_SHOULDER, RIGHT_ELBOW),
    (RIGHT_ELBOW, RIGHT_WRIST),
    # Left leg
    (LEFT_HIP, LEFT_KNEE),
    (LEFT_KNEE, LEFT_ANKLE),
    # Right leg
    (RIGHT_HIP, RIGHT_KNEE),
    (RIGHT_KNEE, RIGHT_ANKLE),
]

FAULT_THRESHOLD = 35.0  # degrees


def compute_xfactor(lms):
    lh, rh = lms[LEFT_HIP],      lms[RIGHT_HIP]
    ls, rs = lms[LEFT_SHOULDER], lms[RIGHT_SHOULDER]
    hip_ang = np.degrees(np.arctan2(rh.y - lh.y, rh.x - lh.x))
    sho_ang = np.degrees(np.arctan2(rs.y - ls.y, rs.x - ls.x))
    return abs(sho_ang - hip_ang)


def draw_skeleton(frame, lms):
    h, w = frame.shape[:2]

    def pt(idx):
        lm = lms[idx]
        return int(lm.x * w), int(lm.y * h)

    for a, b in CONNECTIONS:
        cv2.line(frame, pt(a), pt(b), (0, 255, 120), 2)

    for i in range(len(lms)):
        x, y = pt(i)
        cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)
        cv2.circle(frame, (x, y), 4, (0, 180, 80), 1)


def draw_hud(frame, xfactor, fps, has_pose):
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (360, 120), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    cv2.putText(frame, "Golf Vision  |  Live Pose", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    if has_pose:
        color = (0, 210, 0) if xfactor >= FAULT_THRESHOLD else (0, 50, 255)
        bar_max = 70.0
        bar_w = int(min(xfactor / bar_max, 1.0) * 300)
        cv2.rectangle(frame, (20, 62), (20 + bar_w, 80), color, -1)
        cv2.rectangle(frame, (20, 62), (320, 80), (180, 180, 180), 1)
        thresh_x = int((FAULT_THRESHOLD / bar_max) * 300) + 20
        cv2.line(frame, (thresh_x, 57), (thresh_x, 85), (255, 220, 0), 2)
        cv2.putText(frame, f"X-Factor: {xfactor:.1f} deg  (min {FAULT_THRESHOLD:.0f})",
                    (20, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (200, 200, 200), 1)
        label = "X-Factor OK" if xfactor >= FAULT_THRESHOLD else "FAULT: Low X-Factor"
        cv2.putText(frame, label, (20, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    else:
        cv2.putText(frame, "No pose — step into frame", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 255), 2)

    cv2.putText(frame, f"FPS {fps:.0f}", (w - 80, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
    cv2.putText(frame, "Q to quit", (w - 85, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (130, 130, 130), 1)


def main():
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=os.path.abspath(MODEL_PATH)),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    xfactor = 0.0
    prev_t = time.time()

    with PoseLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            ts_ms = int(time.time() * 1000)

            mp_img = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            )
            result = landmarker.detect_for_video(mp_img, ts_ms)

            has_pose = bool(result.pose_landmarks)
            if has_pose:
                lms = result.pose_landmarks[0]
                draw_skeleton(frame, lms)
                xfactor = compute_xfactor(lms)

            cur_t = time.time()
            fps = 1.0 / max(cur_t - prev_t, 1e-9)
            prev_t = cur_t

            draw_hud(frame, xfactor, fps, has_pose)
            cv2.imshow("Golf Vision — Live Pose", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print("Session ended.")


if __name__ == "__main__":
    main()
