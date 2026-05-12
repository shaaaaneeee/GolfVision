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
    """
    raw_sequence = extract_landmarks(video_path)
    sequence_list = [raw_sequence[k] for k in sorted(raw_sequence.keys())]
    smoothed_list = smooth_landmarks(sequence_list, alpha=0.6)
    smoothed = {i: f for i, f in enumerate(smoothed_list)}

    phases = detect_phases(smoothed)
    features = compute_swing_features(smoothed, phases)
    faults = detect_faults(features)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
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
