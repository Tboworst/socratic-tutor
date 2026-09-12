import uuid
from fastapi import APIRouter, HTTPException
from models.schemas import (
    DiagnoseRequest, DiagnoseResponse,
    RespondRequest, RespondResponse,
    SocraticStage, STAGE_ORDER,
)
from services import llm

router = APIRouter()

# In-memory session store  {session_id -> SessionState dict}
# Fine for hackathon demo; swap for Redis/DB in production
_sessions: dict[str, dict] = {}


def _get_session(session_id: str) -> dict:
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/diagnose", response_model=DiagnoseResponse)
def diagnose(req: DiagnoseRequest):
    """
    Step 1: User submits their code (and optional question).
    The AI diagnoses the bug/concept gap and plans the 5-stage hint ladder.
    Returns the first Socratic question (orientation stage).
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
        "history": [
            {"role": "bot", "stage": "orientation", "content": first_question}
        ],
    }

    return DiagnoseResponse(
        session_id=session_id,
        first_message=first_question,
        current_stage=SocraticStage.ORIENTATION,
    )


@router.post("/respond", response_model=RespondResponse)
def respond(req: RespondRequest):
    """
    Step 2+: User submits an answer to the current Socratic question.
    The AI evaluates:
      - correct answer + correct reasoning  → advance to next stage
      - correct answer + wrong reasoning    → counter-example, stay
      - wrong answer   + correct reasoning  → nudge, stay
      - both wrong                          → hint, stay
    At the final stage (explain), generate a summary note.
    """
    session = _get_session(req.session_id)
    diag = session["diagnosis"]
    stage = session["current_stage"]
    stage_index = session["stage_index"]

    # The question the bot last asked
    last_bot_msg = next(
        (h["content"] for h in reversed(session["history"]) if h["role"] == "bot"),
        diag["hints"][stage.value],
    )

    # Log user answer
    session["history"].append(
        {"role": "user", "stage": stage.value, "content": req.user_answer}
    )

    # Evaluate
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

    feedback = evaluation["feedback"]
    advance = evaluation.get("advance", False)

    # Decide next state
    if advance and stage_index < len(STAGE_ORDER) - 1:
        # Move to next stage
        next_index = stage_index + 1
        next_stage = STAGE_ORDER[next_index]
        next_question = diag["hints"][next_stage.value]
        bot_message = f"{feedback}\n\n{next_question}"

        session["current_stage"] = next_stage
        session["stage_index"] = next_index
        session["attempt"] = 1
        session["history"].append(
            {"role": "bot", "stage": next_stage.value, "content": bot_message}
        )

        return RespondResponse(
            message=bot_message,
            current_stage=next_stage,
            stage_index=next_index,
            is_complete=False,
        )

    elif advance and stage_index == len(STAGE_ORDER) - 1:
        # Final stage complete → generate summary
        session["history"].append(
            {"role": "bot", "stage": stage.value, "content": feedback}
        )
        summary = llm.generate_summary(
            concept_gap=diag["concept_gap"],
            correct_answer=diag["correct_answer"],
            history=session["history"],
        )
        return RespondResponse(
            message=feedback,
            current_stage=stage,
            stage_index=stage_index,
            is_complete=True,
            summary=summary,
        )

    else:
        # Stay on current stage, increment attempt
        session["attempt"] += 1
        session["history"].append(
            {"role": "bot", "stage": stage.value, "content": feedback}
        )

        return RespondResponse(
            message=feedback,
            current_stage=stage,
            stage_index=stage_index,
            is_complete=False,
        )
