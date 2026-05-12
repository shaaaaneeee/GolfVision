import os
import anthropic

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 256


def build_prompt(fault_name: str, severity: float, skill_level: str) -> str:
    """Build the coaching prompt for the given fault and skill level."""
    fault_display = fault_name.replace("_", " ")
    sev_note = "\n- Also recommend seeing a professional instructor." if severity > 0.7 else ""
    return (
        f"You are a PGA-certified golf instructor giving feedback to a {skill_level} golfer.\n\n"
        f"Primary fault detected: {fault_display} (severity: {severity:.2f} out of 1.0)\n\n"
        "Give coaching feedback following these rules:\n"
        "- Focus on this single fault only\n"
        "- Provide one specific physical cue (what to FEEL, not think)\n"
        "- Explain briefly why this hurts ball flight\n"
        "- Maximum 3 sentences\n"
        f"- Encouraging, specific tone{sev_note}"
    )


def generate_coaching(
    faults: dict[str, float],
    skill_level: str = "intermediate",
    client: anthropic.Anthropic | None = None,
) -> str:
    """
    Convert fault dict into natural language coaching advice.
    Focuses on the single highest-severity fault.
    No API call is made when there are no active faults.
    """
    active = {k: v for k, v in faults.items() if v > 0.0}
    if not active:
        return "Great swing! No significant faults detected this session. Keep doing what you're doing."

    top_fault, severity = max(active.items(), key=lambda x: x[1])
    prompt = build_prompt(top_fault, severity, skill_level)

    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required when no client is provided"
            )
        client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError:
        return "Coaching service temporarily unavailable. Please try again."

    if not message.content:
        return "Coaching service returned an empty response. Please try again."
    return message.content[0].text
