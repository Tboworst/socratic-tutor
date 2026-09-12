import uuid
from fastapi import APIRouter, HTTPException
from models.schemas import (
    QuizGenerateRequest, QuizGenerateResponse,
    MCQuestion, MCOption, CodeFixQuestion,
    QuizType,
)
from services import llm

router = APIRouter()

# Store quizzes in memory (quiz_id -> raw quiz dict + metadata)
_quizzes: dict[str, dict] = {}


def _build_response(quiz_id: str, quiz_type: QuizType, raw: dict) -> QuizGenerateResponse:
    if quiz_type == QuizType.MC:
        questions = [
            MCQuestion(
                id=q["id"],
                prompt=q["prompt"],
                options=[
                    MCOption(label=k, text=v)
                    for k, v in (
                        q["options"].items()
                        if isinstance(q["options"], dict)
                        else ((o["label"], o["text"]) for o in q["options"])
                    )
                ],
                correct_label=q["correct_label"],
                explanation=q["explanation"],
            )
            for q in raw["questions"]
        ]
        return QuizGenerateResponse(
            quiz_id=quiz_id,
            quiz_type=quiz_type,
            mc_questions=questions,
        )
    else:
        questions = [
            CodeFixQuestion(
                id=q["id"],
                prompt=q["prompt"],
                buggy_code=q["buggy_code"],
                correct_code=q["correct_code"],
                hint=q["hint"],
                explanation=q["explanation"],
            )
            for q in raw["questions"]
        ]
        return QuizGenerateResponse(
            quiz_id=quiz_id,
            quiz_type=quiz_type,
            code_fix_questions=questions,
        )


@router.post("/generate", response_model=QuizGenerateResponse)
def generate_quiz(req: QuizGenerateRequest):
    """
    Generate a quiz from a code snippet.
    If session_id is provided, the quiz will use the tutor session's concept context.
    """
    # Pull concept context from an active tutor session if given
    context = ""
    if req.session_id:
        # Import here to avoid circular dependency
        from routers.tutor import _sessions
        session = _sessions.get(req.session_id)
        if session:
            diag = session["diagnosis"]
            context = (
                f"This code relates to the concept: {diag['concept_gap']}. "
                f"Focus questions on that concept."
            )

    try:
        raw = llm.generate_quiz(
            code=req.code,
            language=req.language,
            quiz_type=req.quiz_type.value,
            context=context,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    quiz_id = str(uuid.uuid4())
    _quizzes[quiz_id] = {"raw": raw, "quiz_type": req.quiz_type}

    return _build_response(quiz_id, req.quiz_type, raw)
