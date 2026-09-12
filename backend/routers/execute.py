from fastapi import APIRouter, HTTPException

from models.schemas import ExecuteRequest, ExecuteResponse
from services import runner

router = APIRouter()

# Was services.piston; see services/runner.py for why it changed.


@router.post("/", response_model=ExecuteResponse)
def execute_code(req: ExecuteRequest):
    """
    Run a snippet locally and return stdout/stderr/exit_code.

    Sync `def` on purpose: FastAPI then runs it in a threadpool, so a snippet
    that blocks for its whole timeout doesn't stall the event loop.
    """
    try:
        return ExecuteResponse(**runner.execute(req.code, req.language, req.stdin or ""))
    except runner.UnsupportedLanguage:
        raise HTTPException(
            status_code=400,
            detail=f"This tutor only runs Python, not {req.language!r}.",
        )
