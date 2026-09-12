import json
import os
import anthropic
from utils.prompts import (
    DIAGNOSIS_SYSTEM, DIAGNOSIS_PROMPT,
    EVALUATOR_SYSTEM, EVALUATOR_PROMPT,
    SUMMARY_SYSTEM, SUMMARY_PROMPT,
    QUIZ_SYSTEM, QUIZ_PROMPT_MC, QUIZ_PROMPT_CODE_FIX,
    CHALLENGE_SYSTEM, CHALLENGE_PROMPT,
    CHALLENGE_EVALUATE_SYSTEM, CHALLENGE_EVALUATE_PROMPT,
)

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-opus-4-6"


def _ask(system: str, user: str) -> str:
    """Single-turn Claude call, returns text content."""
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


def _parse_json(raw: str) -> dict:
    """Extract JSON from a Claude response (strips markdown fences if present)."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def diagnose(code: str, language: str, question: str) -> dict:
    """
    Returns:
    {
      bug_type, concept_gap, correct_answer,
      hints: { orientation, localization, observation, naming, explain }
    }
    """
    prompt = DIAGNOSIS_PROMPT.format(
        language=language,
        code=code,
        question=question or "I'm not sure what's wrong.",
    )
    raw = _ask(DIAGNOSIS_SYSTEM, prompt)
    return _parse_json(raw)


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
    """
    Returns:
    { answer_correct, reasoning_correct, feedback, advance }
    """
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
    raw = _ask(EVALUATOR_SYSTEM, prompt)
    return _parse_json(raw)


def generate_quiz(*, code: str, language: str, quiz_type: str, context: str = "") -> dict:
    """
    Returns:
      MC:       { questions: [ { id, prompt, options, correct_label, explanation } ] }
      code_fix: { questions: [ { id, prompt, buggy_code, correct_code, hint, explanation } ] }
    """
    if quiz_type == "mc":
        prompt = QUIZ_PROMPT_MC.format(language=language, code=code, context=context)
    else:
        prompt = QUIZ_PROMPT_CODE_FIX.format(language=language, code=code, context=context)
    raw = _ask(QUIZ_SYSTEM, prompt)
    return _parse_json(raw)


def generate_challenge(*, language: str, difficulty: str, num_bugs: int) -> dict:
    """
    Returns:
    { buggy_code, instructions, bugs: [ { id, type, line_hint, description } ] }
    bugs are internal — never sent to the student.
    """
    prompt = CHALLENGE_PROMPT.format(
        language=language,
        difficulty=difficulty,
        num_bugs=num_bugs,
    )
    raw = _ask(CHALLENGE_SYSTEM, prompt)
    return _parse_json(raw)


def evaluate_challenge(
    *,
    language: str,
    buggy_code: str,
    bugs: list[dict],
    fixed_code: str,
) -> dict:
    """
    Returns:
    { results: [ { bug_id, fixed, explanation } ], overall_feedback, score }
    """
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
    raw = _ask(CHALLENGE_EVALUATE_SYSTEM, prompt)
    return _parse_json(raw)


def generate_summary(*, concept_gap: str, correct_answer: str, history: list[dict]) -> str:
    """Returns a final summary string for the student."""
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
