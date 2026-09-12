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

_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()

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
            model=os.getenv("CLAUDE_MODEL", "claude-opus-4-6"),
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text

    # OpenRouter and Ollama share the OpenAI-compatible format
    client = _get_openai_client()
    if _PROVIDER == "openrouter":
        model = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-coder-32b-instruct")
    else:
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def _parse_json(raw: str) -> dict:
    """Strip markdown fences if present, then parse JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def _ask_json(system: str, user: str) -> dict:
    """
    Ask for JSON, and retry ONCE with a stricter instruction if the model
    returns prose. A malformed response used to 500 the whole request --
    the fastest way to lose a live demo.
    """
    raw = _ask(system, user)
    try:
        return _parse_json(raw)
    except (json.JSONDecodeError, IndexError):
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
