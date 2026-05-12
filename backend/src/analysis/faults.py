FAULT_THRESHOLDS: dict[str, tuple[str, str, float]] = {
    # fault_name: (feature_name, operator, threshold)
    "insufficient_x_factor": ("hip_shoulder_sep_at_p5",    "<",  35.0),
    "early_extension":        ("hip_forward_shift_p6_p8",  ">",  0.05),
    "reverse_pivot":          ("weight_trail_at_p5",        "<",  0.55),
}

# Distance past threshold that maps to severity 1.0 (linear scale)
_SEVERITY_SCALE: dict[str, float] = {
    "insufficient_x_factor": 35.0,   # 0° separation → severity 1.0
    "early_extension":        0.10,   # 0.05 threshold + 0.10 scale = 0.15 total shift → severity 1.0
    "reverse_pivot":          0.55,   # 0.0 weight trail → severity 1.0
}


def detect_faults(features: dict[str, float]) -> dict[str, float]:
    """
    Apply rule thresholds to a feature vector.
    Returns {fault_name: severity} where severity is 0.0 (none) to 1.0 (severe).
    Missing features produce 0.0 severity (cannot flag what was not measured).
    """
    results: dict[str, float] = {}

    for fault, (feat, op, thresh) in FAULT_THRESHOLDS.items():
        val = features.get(feat)
        if val is None:
            results[fault] = 0.0
            continue

        if op == "<" and val < thresh:
            raw = (thresh - val) / _SEVERITY_SCALE[fault]
        elif op == ">" and val > thresh:
            raw = (val - thresh) / _SEVERITY_SCALE[fault]
        else:
            raw = 0.0

        results[fault] = round(min(raw, 1.0), 3)

    return results
