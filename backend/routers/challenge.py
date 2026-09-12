import uuid
from fastapi import APIRouter, HTTPException
from models.schemas import (
    ChallengeGenerateRequest, ChallengeGenerateResponse,
    ChallengeSubmitRequest, ChallengeSubmitResponse,
    BugResult,
)
from services import claude

router = APIRouter()

# Store challenges in memory — bugs are internal, never sent to student
# { challenge_id -> { buggy_code, language, bugs, instructions } }
_challenges: dict[str, dict] = {}


@router.post("/generate", response_model=ChallengeGenerateResponse)
def generate_challenge(req: ChallengeGenerateRequest):
    """
    Generate a realistic code snippet with N hidden bugs for interview practice.
    The bugs list is stored server-side; the student only sees the buggy code.
    """
    if not 1 <= req.num_bugs <= 4:
        raise HTTPException(status_code=422, detail="num_bugs must be between 1 and 4")

    raw = claude.generate_challenge(
        language=req.language,
        difficulty=req.difficulty.value,
        num_bugs=req.num_bugs,
    )

    challenge_id = str(uuid.uuid4())
    _challenges[challenge_id] = {
        "buggy_code": raw["buggy_code"],
        "language": req.language,
        "bugs": raw["bugs"],          # internal — not returned to client
        "instructions": raw["instructions"],
    }

    return ChallengeGenerateResponse(
        challenge_id=challenge_id,
        buggy_code=raw["buggy_code"],
        language=req.language,
        num_bugs=req.num_bugs,
        instructions=raw["instructions"],
    )


@router.post("/submit", response_model=ChallengeSubmitResponse)
def submit_challenge(req: ChallengeSubmitRequest):
    """
    Student submits their fixed code.
    AI compares it against the known bugs and reports which ones were caught.
    """
    challenge = _challenges.get(req.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    evaluation = claude.evaluate_challenge(
        language=challenge["language"],
        buggy_code=challenge["buggy_code"],
        bugs=challenge["bugs"],
        fixed_code=req.fixed_code,
    )

    results = [
        BugResult(
            bug_id=r["bug_id"],
            fixed=r["fixed"],
            explanation=r["explanation"],
        )
        for r in evaluation["results"]
    ]

    return ChallengeSubmitResponse(
        score=evaluation["score"],
        total=len(challenge["bugs"]),
        results=results,
        overall_feedback=evaluation["overall_feedback"],
    )
