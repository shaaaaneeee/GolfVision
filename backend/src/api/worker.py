import os
import anthropic
from pose.extractor import extract_landmarks
from pose.smoother import smooth_landmarks
from analysis.phases import detect_phases
from analysis.features import compute_swing_features
from analysis.faults import detect_faults
from feedback.coach import generate_coaching


def run_analysis(
    video_path: str,
    skill_level: str = "intermediate",
) -> dict:
    """
    Full analysis pipeline: video file -> coaching result dict.
    Returns {"faults": {...}, "features": {...}, "coaching": "...", "phases": {...}}
    Returns {"error": "...", "faults": {}, ...} if no person is detected.
    The temp video file is always deleted after processing.
    """
    try:
        raw_sequence = extract_landmarks(video_path)
        if not raw_sequence:
            return {
                "error": "No person detected in video. Ensure the golfer is fully visible and well-lit.",
                "faults": {},
                "features": {},
                "coaching": "Unable to analyze: no golfer detected in the video.",
                "phases": {},
            }

        # Preserve original video frame indices through smoothing
        sorted_keys = sorted(raw_sequence.keys())
        sequence_list = [raw_sequence[k] for k in sorted_keys]
        smoothed_list = smooth_landmarks(sequence_list, alpha=0.6)
        smoothed = {sorted_keys[i]: f for i, f in enumerate(smoothed_list)}

        phases = detect_phases(smoothed)
        features = compute_swing_features(smoothed, phases)
        faults = detect_faults(features)

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        client = anthropic.Anthropic(api_key=api_key)
        coaching = generate_coaching(faults, skill_level=skill_level, client=client)

        return {
            "faults": faults,
            "features": features,
            "coaching": coaching,
            "phases": {
                "p5_frame": phases.p5_frame,
                "p8_frame": phases.p8_frame,
            },
        }
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
