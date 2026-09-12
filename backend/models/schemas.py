from pydantic import BaseModel
from enum import Enum
from typing import Optional


class SocraticStage(str, Enum):
    ORIENTATION = "orientation"
    LOCALIZATION = "localization"
    OBSERVATION = "observation"
    NAMING = "naming"
    EXPLAIN = "explain"


STAGE_ORDER = [
    SocraticStage.ORIENTATION,
    SocraticStage.LOCALIZATION,
    SocraticStage.OBSERVATION,
    SocraticStage.NAMING,
    SocraticStage.EXPLAIN,
]


# --- Tutor ---

class DiagnoseRequest(BaseModel):
    code: str
    language: str
    question: Optional[str] = None


class DiagnoseResponse(BaseModel):
    session_id: str
    first_message: str  # The first Socratic question (orientation stage)
    current_stage: SocraticStage


class RespondRequest(BaseModel):
    session_id: str
    user_answer: str


class RespondResponse(BaseModel):
    message: str               # Bot's reply
    current_stage: SocraticStage
    stage_index: int           # 0-4, for progress bar
    is_complete: bool
    summary: Optional[str] = None   # Final note when session ends


# --- Code execution ---

class ExecuteRequest(BaseModel):
    code: str
    language: str
    stdin: Optional[str] = ""


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
