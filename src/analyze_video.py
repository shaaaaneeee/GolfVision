"""
Golf Vision — Video Analysis
Run pose estimation on an uploaded golf swing video.
Saves annotated output video + landmark JSON.

Usage:
    python src/analyze_video.py --video input/swing.mp4
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import os
import json
import argparse

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
    (LEFT_SHOULDER, RIGHT_SHOULDER),
    (LEFT_SHOULDER, LEFT_HIP),
    (RIGHT_SHOULDER, RIGHT_HIP),
    (LEFT_HIP, RIGHT_HIP),
    (LEFT_SHOULDER, LEFT_ELBOW),
    (LEFT_ELBOW, LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW),
    (RIGHT_ELBOW, RIGHT_WRIST),
    (LEFT_HIP, LEFT_KNEE),
    (LEFT_KNEE, LEFT_ANKLE),
    (RIGHT_HIP, RIGHT_KNEE),
    (RIGHT_KNEE, RIGHT_ANKLE),
]

FAULT_THRESHOLD = 35.0


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


def draw_hud(frame, xfactor, frame_idx, total_frames, has_pose):
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (380, 125), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    cv2.putText(frame, "Golf Vision  |  Swing Analysis", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    # Progress bar
    progress = frame_idx / max(total_frames - 1, 1)
    bar_w = int(progress * 340)
    cv2.rectangle(frame, (20, 42), (20 + bar_w, 50), (80, 180, 255), -1)
    cv2.rectangle(frame, (20, 42), (360, 50), (100, 100, 100), 1)

    if has_pose:
        color = (0, 210, 0) if xfactor >= FAULT_THRESHOLD else (0, 50, 255)
        bar_max = 70.0
        xbar_w = int(min(xfactor / bar_max, 1.0) * 320)
        cv2.rectangle(frame, (20, 68), (20 + xbar_w, 85), color, -1)
        cv2.rectangle(frame, (20, 68), (340, 85), (180, 180, 180), 1)
        thresh_x = int((FAULT_THRESHOLD / bar_max) * 320) + 20
        cv2.line(frame, (thresh_x, 63), (thresh_x, 90), (255, 220, 0), 2)
        cv2.putText(frame, f"X-Factor: {xfactor:.1f} deg  (min {FAULT_THRESHOLD:.0f})",
                    (20, 63), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (200, 200, 200), 1)
        label = "X-Factor OK" if xfactor >= FAULT_THRESHOLD else "FAULT: Low X-Factor"
        cv2.putText(frame, label, (20, 114),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    else:
        cv2.putText(frame, "No pose detected", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 255), 2)

    cv2.putText(frame, f"Frame {frame_idx}/{total_frames}", (w - 160, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)


def analyze(video_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(video_path))[0]
    out_video_path = os.path.join(output_dir, f"{base}_analyzed.mp4")
    out_json_path  = os.path.join(output_dir, f"{base}_landmarks.json")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    fps        = cap.get(cv2.CAP_PROP_FPS) or 30
    width      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_video_path, fourcc, fps, (width, height))

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=os.path.abspath(MODEL_PATH)),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    landmarks_log = {}
    xfactors = []
    frame_idx = 0
    start = time.time()

    print(f"\nAnalyzing: {video_path}")
    print(f"Resolution: {width}x{height} @ {fps:.0f}fps  |  {total_frames} frames\n")

    with PoseLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            ts_ms = int((frame_idx / fps) * 1000)
            mp_img = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            )
            result = landmarker.detect_for_video(mp_img, ts_ms)

            has_pose = bool(result.pose_landmarks)
            xfactor = 0.0

            if has_pose:
                lms = result.pose_landmarks[0]
                draw_skeleton(frame, lms)
                xfactor = compute_xfactor(lms)
                xfactors.append(xfactor)
                landmarks_log[frame_idx] = {
                    "xfactor": round(xfactor, 3),
                    "landmarks": [
                        {"x": round(lm.x, 4), "y": round(lm.y, 4), "z": round(lm.z, 4)}
                        for lm in lms
                    ]
                }

            draw_hud(frame, xfactor, frame_idx, total_frames, has_pose)
            writer.write(frame)

            frame_idx += 1
            if frame_idx % 30 == 0 or frame_idx == total_frames:
                pct = frame_idx / total_frames * 100
                elapsed = time.time() - start
                eta = (elapsed / frame_idx) * (total_frames - frame_idx)
                print(f"  [{pct:5.1f}%] Frame {frame_idx}/{total_frames}  "
                      f"ETA: {eta:.1f}s  X-Factor: {xfactor:.1f} deg")

    cap.release()
    writer.release()

    # Save landmarks JSON
    with open(out_json_path, 'w') as f:
        json.dump(landmarks_log, f, indent=2)

    # Summary
    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"Done in {elapsed:.1f}s")
    print(f"Output video : {out_video_path}")
    print(f"Landmarks JSON: {out_json_path}")

    if xfactors:
        peak = max(xfactors)
        avg  = np.mean(xfactors)
        print(f"\n--- X-Factor Summary ---")
        print(f"  Peak:    {peak:.1f} deg")
        print(f"  Average: {avg:.1f} deg")
        if peak < FAULT_THRESHOLD:
            sev = round((FAULT_THRESHOLD - peak) / FAULT_THRESHOLD, 2)
            print(f"  FAULT: Insufficient X-Factor (severity: {sev})")
            print(f"  Tip: Focus on turning shoulders while resisting with hips on backswing.")
        else:
            print(f"  X-Factor: Within acceptable range.")
    print('='*50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Golf Vision — Video Swing Analyzer")
    parser.add_argument("--video",  required=True, help="Path to input video file")
    parser.add_argument("--outdir", default="output", help="Output directory")
    args = parser.parse_args()
    analyze(args.video, args.outdir)
