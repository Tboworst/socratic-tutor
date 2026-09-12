"""
Provider-agnostic LLM service.

Set LLM_PROVIDER in .env to switch backends:
  claude      → Anthropic API     (requires ANTHROPIC_API_KEY)
  openrouter  → OpenRouter API    (requires OPENROUTER_API_KEY)
  ollama      → local Ollama      (requires Ollama running on OLLAMA_BASE_URL)
"""
import json
import os

from utils.prompts import (
    DIAGNOSIS_SYSTEM, DIAGNOSIS_PROMPT,
    EVALUATOR_SYSTEM, EVALUATOR_PROMPT,
    SUMMARY_SYSTEM, SUMMARY_PROMPT,
    QUIZ_SYSTEM, QUIZ_PROMPT_MC, QUIZ_PROMPT_CODE_FIX,
    CHALLENGE_SYSTEM, CHALLENGE_PROMPT,
    CHALLENGE_EVALUATE_SYSTEM, CHALLENGE_EVALUATE_PROMPT,
)

_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()

# ── Lazy client cache (one instance per provider) ────────────────────────────

_claude_client = None
_openai_client = None


def _get_claude_client():
    global _claude_client
    if _claude_client is None:
        import anthropic
        _claude_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _claude_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        if _PROVIDER == "openrouter":
            _openai_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
            )
        else:  # ollama
            _openai_client = OpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                api_key="ollama",  # Ollama ignores this but the SDK requires it
            )
    return _openai_client


# ── Core dispatcher ──────────────────────────────────────────────────────────

def _ask(system: str, user: str) -> str:
    """Single-turn LLM call. Routes to the configured provider."""
    if _PROVIDER == "claude":
        client = _get_claude_client()
        msg = client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5"),
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = next((b.text for b in msg.content if getattr(b, "type", "") == "text"), None)
        if not text:
            raise RuntimeError(f"{msg.model} returned no text block (stop_reason={msg.stop_reason!r}).")
        return text

    # OpenRouter and Ollama share the OpenAI-compatible format
    client = _get_openai_client()
    if _PROVIDER == "openrouter":
        model = os.getenv("OPENROUTER_MODEL", "inclusionai/ling-3.0-flash-vl:free")
    else:
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    response = client.chat.completions.create(
        model=model,
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    choice = response.choices[0]
    text = choice.message.content

    # Reasoning models leave content null and put their output in a separate
    # field; some providers return a refusal instead. Without this, a null
    # content surfaced as an opaque AttributeError two frames later.
    if not text:
        text = getattr(choice.message, "reasoning", None) or getattr(
            choice.message, "refusal", None
        )

    if not text:
        reason = getattr(choice, "finish_reason", None)
        hint = (
            " The reasoning consumed the whole token budget -- raise LLM_MAX_TOKENS "
            "or pick a non-reasoning model."
            if reason == "length"
            else " Try a different model."
        )
        raise RuntimeError(
            f"{model} returned no text (finish_reason={reason!r})." + hint
        )

    return text


def _parse_json(raw: str) -> dict:
    """
    Strip markdown fences, then parse JSON.

    Weaker models like to wrap the object in a sentence ("Here is the JSON:"),
    so as a last resort we take everything between the first { and the last }.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"expected a JSON string, got {raw!r}")

    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) > 1:
            raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(raw[start : end + 1])


def _ask_json(system: str, user: str) -> dict:
    """
    Ask for JSON, and retry ONCE with a stricter instruction if the model
    returns prose. A malformed response used to 500 the whole request --
    the fastest way to lose a live demo.
    """
    raw = _ask(system, user)
    try:
        return _parse_json(raw)
    except (json.JSONDecodeError, IndexError, ValueError):
        retry_system = system + "\n\nCRITICAL: output raw JSON only. No prose, no markdown fences."
        raw = _ask(retry_system, user)
        return _parse_json(raw)


# ── Public functions (identical interface regardless of provider) ─────────────

def diagnose(code: str, language: str, question: str) -> dict:
    prompt = DIAGNOSIS_PROMPT.format(
        language=language,
        code=code,
        question=question or "I'm not sure what's wrong.",
    )
    return _ask_json(DIAGNOSIS_SYSTEM, prompt)


def evaluate(
    *,
    language: str,
    bug_type: str,
    concept_gap: str,
    correct_answer: str,
    stage: str,
    question_asked: str,
    user_answer: str,
    attempt: int,
) -> dict:
    prompt = EVALUATOR_PROMPT.format(
        language=language,
        bug_type=bug_type,
        concept_gap=concept_gap,
        correct_answer=correct_answer,
        stage=stage,
        question_asked=question_asked,
        user_answer=user_answer,
        attempt=attempt,
    )
    return _ask_json(EVALUATOR_SYSTEM, prompt)


def generate_quiz(*, code: str, language: str, quiz_type: str, context: str = "") -> dict:
    if quiz_type == "mc":
        prompt = QUIZ_PROMPT_MC.format(language=language, code=code, context=context)
    else:
        prompt = QUIZ_PROMPT_CODE_FIX.format(language=language, code=code, context=context)
    return _ask_json(QUIZ_SYSTEM, prompt)


def generate_challenge(*, language: str, difficulty: str, num_bugs: int) -> dict:
    prompt = CHALLENGE_PROMPT.format(
        language=language,
        difficulty=difficulty,
        num_bugs=num_bugs,
    )
    return _ask_json(CHALLENGE_SYSTEM, prompt)


def evaluate_challenge(
    *,
    language: str,
    buggy_code: str,
    bugs: list[dict],
    fixed_code: str,
) -> dict:
    bugs_description = "\n".join(
        f"- {b['id']} ({b['type']}, {b['line_hint']}): {b['description']}"
        for b in bugs
    )
    prompt = CHALLENGE_EVALUATE_PROMPT.format(
        language=language,
        buggy_code=buggy_code,
        bugs_description=bugs_description,
        fixed_code=fixed_code,
    )
    return _ask_json(CHALLENGE_EVALUATE_SYSTEM, prompt)


def generate_summary(*, concept_gap: str, correct_answer: str, history: list[dict]) -> str:
    history_text = "\n".join(
        f"[{h['role'].upper()}] ({h.get('stage', '')}): {h['content']}"
        for h in history
    )
    prompt = SUMMARY_PROMPT.format(
        concept_gap=concept_gap,
        correct_answer=correct_answer,
        history=history_text,
    )
    return _ask(SUMMARY_SYSTEM, prompt)
