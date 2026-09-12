"""
Provider-agnostic LLM service.

Set LLM_PROVIDER in .env to switch backends:
  claude      → Anthropic API     (requires ANTHROPIC_API_KEY)
  openrouter  → OpenRouter API    (requires OPENROUTER_API_KEY)
  ollama      → local Ollama      (requires Ollama running on OLLAMA_BASE_URL)
"""
import json
import os
import time

from utils.prompts import (
    DIAGNOSIS_SYSTEM, DIAGNOSIS_PROMPT,
    EVALUATOR_SYSTEM, EVALUATOR_PROMPT,
    SUMMARY_SYSTEM, SUMMARY_PROMPT,
    QUIZ_SYSTEM, QUIZ_PROMPT_MC, QUIZ_PROMPT_CODE_FIX,
    CHALLENGE_SYSTEM, CHALLENGE_PROMPT,
    CHALLENGE_EVALUATE_SYSTEM, CHALLENGE_EVALUATE_PROMPT,
)

_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()

# --- What changed here, and why -------------------------------------------
# * _ask retries once on a transient provider error and falls back to the
#   reasoning/refusal fields, which is where some models put their output
#   while leaving content null. A null content used to surface three frames
#   later as "AttributeError: 'NoneType' has no attribute 'strip'".
# * Malformed JSON is retried once with a stricter instruction, and parsed
#   from the first { to the last } as a last resort.
# * Default model IDs updated: claude-opus-4-6 no longer exists, and the
#   OpenRouter fallback named a paid model.
# --------------------------------------------------------------------------

# Free pools upstream of OpenRouter saturate without warning, so a 429 there
# is usually not our own quota.
_TRANSIENT = {429, 500, 502, 503, 529}


class ProviderUnavailable(Exception):
    """The provider refused the call for a reason that is not our bug."""

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

def _ask(system: str, user: str, max_tokens: int | None = None) -> str:
    """Single-turn call, retried once on a transient provider error."""
    try:
        return _ask_once(system, user, max_tokens)
    except Exception as e:
        status = getattr(e, "status_code", None)
        if status not in _TRANSIENT:
            raise
        time.sleep(0.5)
        try:
            return _ask_once(system, user, max_tokens)
        except Exception as e2:
            status = getattr(e2, "status_code", status)
            raise ProviderUnavailable(
                f"The model provider is refusing calls right now (HTTP {status}). "
                "On a free model this is usually the shared upstream pool being "
                "saturated rather than your own quota. Retry in a moment, switch "
                "OPENROUTER_MODEL, or set LLM_PROVIDER=claude with an API key."
            ) from e2


def _ask_once(system: str, user: str, max_tokens: int | None = None) -> str:
    """One attempt, routed to the configured provider."""
    tokens = max_tokens or int(os.getenv("LLM_MAX_TOKENS", "2048"))

    if _PROVIDER == "claude":
        client = _get_claude_client()
        msg = client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5"),
            max_tokens=tokens,
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
        max_tokens=tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    choice = response.choices[0]
    text = choice.message.content

    # Reasoning models leave content null and put the text elsewhere.
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
    """Strip fences, then parse. Falls back to the span between { and }, since
    weaker models like to wrap the object in a sentence."""
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


def _ask_json(system: str, user: str, max_tokens: int | None = None) -> dict:
    """Ask for JSON; retry once with a stricter instruction if it returns prose."""
    raw = _ask(system, user, max_tokens)
    try:
        return _parse_json(raw)
    except (json.JSONDecodeError, IndexError, ValueError):
        retry_system = system + "\n\nCRITICAL: output raw JSON only. No prose, no markdown fences."
        raw = _ask(retry_system, user, max_tokens)
        return _parse_json(raw)


# ── Public functions (identical interface regardless of provider) ─────────────

_EXECUTABLE = {"python", "py", "python3"}

def diagnose(code: str, language: str, question: str) -> dict:
    can_run = language.lower() in _EXECUTABLE
    exec_note = (
        ""
        if can_run
        else (
            f"\nNOTE: {language} code cannot be executed in this environment. "
            "For the 'observation' hint, do NOT say 'run' or 'print'. Instead, "
            "ask the student to mentally trace a specific expression and predict "
            "what value it holds at that point in the program."
        )
    )
    prompt = DIAGNOSIS_PROMPT.format(
        language=language,
        code=code,
        question=question or "I'm not sure what's wrong.",
        exec_note=exec_note,
    )
    return _ask_json(DIAGNOSIS_SYSTEM, prompt, max_tokens=900)


def evaluate(
    *,
    language: str,
    bug_type: str,
    concept_gap: str,
    correct_answer: str,
    root_cause: str,
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
        root_cause=root_cause,
        stage=stage,
        question_asked=question_asked,
        user_answer=user_answer,
        attempt=attempt,
    )
    return _ask_json(EVALUATOR_SYSTEM, prompt, max_tokens=350)


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
    return _ask(SUMMARY_SYSTEM, prompt, max_tokens=500)
