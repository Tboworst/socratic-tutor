"""
State-machine tests for the Socratic ladder. No LLM, no network, no quota.

The tutor's value is entirely in how it moves between rungs, so that logic
needs to be testable without an API key. Every LLM entry point is stubbed and
we assert on the branch, the stage and the descent count.

Run from backend/:   python test_ladder.py
"""
import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

import main
from routers import tutor
from services import llm

# Keep the tests off the real session file.
tutor._STORE = Path(tempfile.gettempdir()) / "rung_test_sessions.json"
tutor._sessions.clear()

FAKE_DIAGNOSIS = {
    "bug_type": "type coercion",
    "concept_gap": "a string of digits is not a number",
    "correct_answer": "wrap quantity in int() before multiplying",
    "hints": {
        "orientation": "Q1 orientation",
        "localization": "Q2 localization",
        "observation": "Q3 observation",
        "naming": "Q4 naming",
        "explain": "Q5 explain",
        "run_this": "print(type(quantity))",
    },
}

# What the stubbed evaluator will return on the next call.
_next_eval: dict = {}


def _fake_diagnose(**_kwargs):
    return FAKE_DIAGNOSIS


def _fake_evaluate(**_kwargs):
    return dict(_next_eval)


def _fake_summary(**_kwargs):
    return "stub summary"


llm.diagnose = _fake_diagnose
llm.evaluate = _fake_evaluate
llm.generate_summary = _fake_summary

client = TestClient(main.app)

CODE = 'quantity = "3"\nprint(quantity * 5)\n'
PASSED = 0


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        raise AssertionError(f"{label}: got {got!r}, wanted {want!r}")
    PASSED += 1
    print(f"  ok  {label}")


def start() -> str:
    r = client.post(
        "/api/tutor/diagnose",
        json={"code": CODE, "language": "python", "question": "why 33333?"},
    )
    assert r.status_code == 200, r.text
    d = r.json()
    check("diagnose starts at rung 1", d["stage_index"], 0)
    check("diagnose asks the orientation question", d["first_message"], "Q1 orientation")
    check("diagnose reports total rungs", d["total_stages"], 5)
    return d["session_id"]


def answer(sid: str, ev: dict, i_dont_know: bool = False) -> dict:
    global _next_eval
    _next_eval = ev
    r = client.post(
        "/api/tutor/respond",
        json={"session_id": sid, "user_answer": "an answer", "i_dont_know": i_dont_know},
    )
    assert r.status_code == 200, r.text
    return r.json()


RIGHT = {"answer_correct": True, "reasoning_correct": True, "is_guessing": False,
         "feedback": "fb", "advance": True}
RIGHT_BAD_REASON = {"answer_correct": True, "reasoning_correct": False, "is_guessing": False,
                    "feedback": "fb", "advance": False}
WRONG_GOOD_REASON = {"answer_correct": False, "reasoning_correct": True, "is_guessing": False,
                     "feedback": "fb", "advance": False}
BOTH_WRONG = {"answer_correct": False, "reasoning_correct": False, "is_guessing": False,
              "feedback": "fb", "advance": False}
GUESS = {"answer_correct": False, "reasoning_correct": False, "is_guessing": True,
         "feedback": "fb", "advance": False}
# A guess the evaluator still credits with some reasoning. This is the case the
# guess counter exists for: on its own it would keep the student pinned to the
# same rung forever, so two in a row must force a descent.
GUESS_NUDGE = {"answer_correct": False, "reasoning_correct": True, "is_guessing": True,
               "feedback": "fb", "advance": False}

print("\n[1] the four branches")
sid = start()

r = answer(sid, RIGHT_BAD_REASON)
check("right answer + wrong reasoning -> counter_example", r["branch"], "counter_example")
check("  and it does NOT advance", r["stage_index"], 0)
check("  and it is not complete", r["is_complete"], False)
check("  feedback and question are separate fields", r["question"], "Q1 orientation")

r = answer(sid, WRONG_GOOD_REASON)
check("wrong answer + good reasoning -> nudge", r["branch"], "nudge")
check("  and it stays on the rung", r["stage_index"], 0)

r = answer(sid, BOTH_WRONG)
check("both wrong -> descend", r["branch"], "descend")
check("  and it moves to the next rung", r["stage_index"], 1)
check("  and it counts as help given", r["descents"], 1)

r = answer(sid, RIGHT)
check("right + right -> advance", r["branch"], "advance")
check("  and it moves on", r["stage_index"], 2)
check("  without adding a descent", r["descents"], 1)
check("  observation rung ships something to run", r["run_this"], "print(type(quantity))")

print("\n[2] I don't know skips the LLM and drops a rung")
sid = start()
r = answer(sid, BOTH_WRONG, i_dont_know=True)
check("branch is descend", r["branch"], "descend")
check("flagged as an honest admission", r["said_i_dont_know"], True)
check("not scored as a wrong answer", r["answer_correct"], False)
check("not scored as guessing", r["is_guessing"], False)
check("moved down a rung", r["stage_index"], 1)

print("\n[3] guessing")
sid = start()
r = answer(sid, GUESS)
check("a wrong blind guess descends at once -- descending IS the extra help",
      r["branch"], "descend")
check("  and it is recorded as guessing", r["is_guessing"], True)

sid = start()
r = answer(sid, GUESS_NUDGE)
check("one credited guess stays on the rung", r["branch"], "nudge")
check("  so the student can think again", r["stage_index"], 0)
r = answer(sid, GUESS_NUDGE)
check("two in a row force a descent instead of pinning them", r["branch"], "descend")
check("  and they move on", r["stage_index"], 1)
r = answer(sid, GUESS_NUDGE)
check("the counter resets, so the next one is a nudge again", r["branch"], "nudge")

print("\n[4] the ladder terminates and reports")
sid = start()
for expected_stage in (1, 2, 3, 4):
    r = answer(sid, RIGHT)
    check(f"advanced to rung {expected_stage + 1}", r["stage_index"], expected_stage)
    check(f"  still running at rung {expected_stage + 1}", r["is_complete"], False)
r = answer(sid, RIGHT)
check("last rung completes the session", r["is_complete"], True)
check("  branch is terminate", r["branch"], "terminate")
check("  a summary comes back", "stub summary" in (r["summary"] or ""), True)
check("  the summary names the outcome", "Solved on rung 5" in (r["summary"] or ""), True)

print("\n[5] an unknown session 404s rather than crashing")
r = client.post(
    "/api/tutor/respond",
    json={"session_id": "does-not-exist", "user_answer": "x", "i_dont_know": False},
)
check("status", r.status_code, 404)

print("\n[6] sessions survive a restart")
sid = start()
answer(sid, RIGHT)
saved = json.loads(tutor._STORE.read_text(encoding="utf-8"))
check("session written to disk", sid in saved, True)
tutor._sessions.clear()
tutor._restore()
check("session restored into memory", sid in tutor._sessions, True)
r = answer(sid, RIGHT)
check("and it still answers after the restore", r["is_complete"], False)

print(f"\n{PASSED} checks passed.\n")
