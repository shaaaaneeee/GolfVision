import pytest
from unittest.mock import MagicMock, patch
from feedback.coach import build_prompt, generate_coaching


def test_build_prompt_includes_fault_name():
    prompt = build_prompt("early_extension", 0.82, "intermediate")
    assert "early extension" in prompt.lower()


def test_build_prompt_includes_severity():
    prompt = build_prompt("early_extension", 0.82, "intermediate")
    assert "0.82" in prompt


def test_build_prompt_includes_skill_level():
    prompt = build_prompt("reverse_pivot", 0.50, "beginner")
    assert "beginner" in prompt.lower()


def test_generate_coaching_returns_string_from_api():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Feel the pressure in your trail heel.")]
    )
    result = generate_coaching(
        {"early_extension": 0.82, "reverse_pivot": 0.2},
        skill_level="intermediate",
        client=mock_client,
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_coaching_no_faults_returns_positive():
    mock_client = MagicMock()
    result = generate_coaching({}, skill_level="intermediate", client=mock_client)
    assert "no" in result.lower() or "great" in result.lower()
    mock_client.messages.create.assert_not_called()


def test_generate_coaching_picks_highest_severity():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Keep your head still.")]
    )
    generate_coaching(
        {"early_extension": 0.3, "reverse_pivot": 0.9},
        skill_level="advanced",
        client=mock_client,
    )
    call_args = mock_client.messages.create.call_args
    prompt_text = call_args.kwargs["messages"][0]["content"]
    assert "reverse pivot" in prompt_text.lower()


def test_generate_coaching_raises_on_missing_api_key(monkeypatch):
    """When no client is provided and ANTHROPIC_API_KEY is absent, raise ValueError."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        generate_coaching({"early_extension": 0.5})
