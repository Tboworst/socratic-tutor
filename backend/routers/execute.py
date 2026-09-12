from fastapi import APIRouter, HTTPException
from models.schemas import ExecuteRequest, ExecuteResponse
from services import piston
import httpx

router = APIRouter()


@router.post("/", response_model=ExecuteResponse)
async def execute_code(req: ExecuteRequest):
    """Run code via the Piston API and return stdout/stderr/exit_code."""
    try:
        result = await piston.execute(
            code=req.code,
            language=req.language,
            stdin=req.stdin or "",
        )
        return ExecuteResponse(**result)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Piston API error: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Could not reach execution engine: {str(e)}")
