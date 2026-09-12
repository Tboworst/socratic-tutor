import uuid
from fastapi import APIRouter, HTTPException
from models.schemas import (
    DiagnoseRequest, DiagnoseResponse,
    RespondRequest, RespondResponse,
    SocraticStage, STAGE_ORDER, Branch,
)
from services import llm

router = APIRouter()

# In-memory session store  {session_id -> SessionState dict}
# Fine for hackathon demo; swap for Redis/DB in production
_sessions: dict[str, dict] = {}

# Two blind guesses in a row and we stop making the student flail.
GUESS_LIMIT = 2
LAST_INDEX = len(STAGE_ORDER) - 1


def _get_session(session_id: str) -> dict:
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _classify(answer_correct: bool, reasoning_correct: bool) -> Branch:
    """
    The two axes, kept separate. The second case is the whole point of the
    product: the exact symptom of leaning on AI is a right answer with no
    reasoning behind it, and nothing else we could build detects that.
    """
    if answer_correct and reasoning_correct:
        return Branch.ADVANCE
    if answer_correct and not reasoning_correct:
        return Branch.COUNTER_EXAMPLE
    if not answer_correct and reasoning_correct:
        return Branch.NUDGE
    return Branch.DESCEND


def _run_this(session: dict, stage: SocraticStage) -> str | None:
    """The observation rung needs something concrete to execute."""
    if stage != SocraticStage.OBSERVATION:
        return None
    return session["diagnosis"].get("hints", {}).get("run_this")


def _summarise(session: dict, solved: bool) -> str:
    diag = session["diagnosis"]
    descents = session["descents"]
    if solved and descents == 0:
        header = f"Solved on rung {session['stage_index'] + 1} of 5, unaided."
    elif solved:
        header = (
            f"Solved on rung {session['stage_index'] + 1} of 5, "
            f"after {descents} step{'s' if descents != 1 else ''} of extra help."
        )
    else:
        header = "Taught — you reached the last rung and we walked you through it."

    body = llm.generate_summary(
        concept_gap=diag["concept_gap"],
        correct_answer=diag["correct_answer"],
        history=session["history"],
    )
    return f"{header}\n\nConcept: {diag['concept_gap']}\n\n{body}"


@router.post("/diagnose", response_model=DiagnoseResponse)
def diagnose(req: DiagnoseRequest):
    """
    Step 1: the student submits code (and an optional question).
    One LLM call finds the bug, names the concept gap, and plans the whole
    5-rung ladder up front -- so the tutor always knows where it is going.
    Returns the first Socratic question only.
    """
    diagnosis = llm.diagnose(
        code=req.code,
        language=req.language,
        question=req.question or "",
    )

    session_id = str(uuid.uuid4())
    first_question = diagnosis["hints"]["orientation"]

    _sessions[session_id] = {
        "language": req.language,
        "code": req.code,
        "diagnosis": diagnosis,          # bug_type, concept_gap, correct_answer, hints
        "current_stage": SocraticStage.ORIENTATION,
        "stage_index": 0,
        "attempt": 1,                    # attempt count at current stage
        "consecutive_guesses": 0,
        "descents": 0,
        "history": [
            {"role": "bot", "stage": "orientation", "content": first_question}
        ],
    }

    return DiagnoseResponse(
        session_id=session_id,
        first_message=first_question,
        current_stage=SocraticStage.ORIENTATION,
        stage_index=0,
        total_stages=len(STAGE_ORDER),
        bug_type=diagnosis.get("bug_type"),
    )


@router.post("/respond", response_model=RespondResponse)
def respond(req: RespondRequest):
    """
    Step 2+: the student answers the current question.

    Both axes are evaluated and reported separately, so the UI can render
    four visually distinct outcomes instead of one blob of chat text:
      right + right reasoning  -> advance
      right + WRONG reasoning  -> counter-example, stay on this rung
      wrong + right reasoning  -> nudge, stay on this rung
      both wrong               -> descend, i.e. give more help

    "I don't know" skips the LLM entirely and descends. Saying so is the most
    useful answer a stuck student can give; it is never scored as a failure.
    """
    session = _get_session(req.session_id)
    diag = session["diagnosis"]
    stage: SocraticStage = session["current_stage"]
    stage_index: int = session["stage_index"]

    last_bot_msg = next(
        (h["content"] for h in reversed(session["history"]) if h["role"] == "bot"),
        diag["hints"][stage.value],
    )

    session["history"].append({
        "role": "user",
        "stage": stage.value,
        "content": "(I don't know)" if req.i_dont_know else req.user_answer,
    })

    # ---- decide the branch -------------------------------------------------
    if req.i_dont_know:
        answer_correct = reasoning_correct = False
        is_guessing = False
        feedback = (
            "Saying you don't know is the most useful answer you could have given. "
            "Let's drop down a rung."
        )
        branch = Branch.TERMINATE if stage_index == LAST_INDEX else Branch.DESCEND
        session["consecutive_guesses"] = 0
    else:
        evaluation = llm.evaluate(
            language=session["language"],
            bug_type=diag["bug_type"],
            concept_gap=diag["concept_gap"],
            correct_answer=diag["correct_answer"],
            stage=stage.value,
            question_asked=last_bot_msg,
            user_answer=req.user_answer,
            attempt=session["attempt"],
        )
        answer_correct = bool(evaluation.get("answer_correct"))
        reasoning_correct = bool(evaluation.get("reasoning_correct"))
        is_guessing = bool(evaluation.get("is_guessing"))
        feedback = evaluation.get("feedback", "")
        branch = _classify(answer_correct, reasoning_correct)

        # Two blind guesses in a row: stop asking, start helping.
        session["consecutive_guesses"] = (
            session["consecutive_guesses"] + 1 if is_guessing else 0
        )
        if session["consecutive_guesses"] >= GUESS_LIMIT and branch in (
            Branch.COUNTER_EXAMPLE, Branch.NUDGE, Branch.DESCEND
        ):
            branch = Branch.DESCEND
            session["consecutive_guesses"] = 0

        # Last rung: the LLM decides when the student has understood.
        if stage_index == LAST_INDEX and (
            branch == Branch.ADVANCE or evaluation.get("advance") or session["attempt"] >= 2
        ):
            branch = Branch.TERMINATE

    moves_on = branch in (Branch.ADVANCE, Branch.DESCEND)
    if branch == Branch.DESCEND:
        session["descents"] += 1

    # ---- terminal ----------------------------------------------------------
    if branch == Branch.TERMINATE or (moves_on and stage_index == LAST_INDEX):
        solved = answer_correct and reasoning_correct
        session["history"].append(
            {"role": "bot", "stage": stage.value, "content": feedback}
        )
        return RespondResponse(
            message=feedback,
            question=None,
            current_stage=stage,
            stage_index=stage_index,
            total_stages=len(STAGE_ORDER),
            is_complete=True,
            summary=_summarise(session, solved),
            answer_correct=answer_correct,
            reasoning_correct=reasoning_correct,
            is_guessing=is_guessing,
            branch=Branch.TERMINATE,
            descents=session["descents"],
            said_i_dont_know=req.i_dont_know,
        )

    # ---- next rung ---------------------------------------------------------
    if moves_on:
        stage_index += 1
        stage = STAGE_ORDER[stage_index]
        next_question = diag["hints"][stage.value]
        session["current_stage"] = stage
        session["stage_index"] = stage_index
        session["attempt"] = 1
    else:
        # Same rung, another go. The question stays on screen.
        session["attempt"] += 1
        next_question = diag["hints"][stage.value]

    session["history"].append(
        {"role": "bot", "stage": stage.value, "content": f"{feedback}\n\n{next_question}"}
    )

    return RespondResponse(
        message=feedback,
        question=next_question,
        current_stage=stage,
        stage_index=stage_index,
        total_stages=len(STAGE_ORDER),
        is_complete=False,
        answer_correct=answer_correct,
        reasoning_correct=reasoning_correct,
        is_guessing=is_guessing,
        branch=branch,
        descents=session["descents"],
        said_i_dont_know=req.i_dont_know,
        run_this=_run_this(session, stage),
    )
