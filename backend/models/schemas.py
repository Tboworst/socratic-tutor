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


# --- Quiz ---

class QuizType(str, Enum):
    MC = "mc"
    CODE_FIX = "code_fix"


class QuizGenerateRequest(BaseModel):
    code: str
    language: str
    quiz_type: QuizType = QuizType.MC
    session_id: Optional[str] = None   # optional: pulls concept context from tutor session


class MCOption(BaseModel):
    label: str   # "A", "B", "C", "D"
    text: str


class MCQuestion(BaseModel):
    id: str
    prompt: str
    options: list[MCOption]
    correct_label: str    # "A" / "B" / "C" / "D"
    explanation: str


class CodeFixQuestion(BaseModel):
    id: str
    prompt: str
    buggy_code: str
    correct_code: str
    hint: str
    explanation: str


class QuizGenerateResponse(BaseModel):
    quiz_id: str
    quiz_type: QuizType
    mc_questions: Optional[list[MCQuestion]] = None
    code_fix_questions: Optional[list[CodeFixQuestion]] = None


# --- Challenge (interview bug-finder) ---

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ChallengeGenerateRequest(BaseModel):
    language: str
    difficulty: Difficulty = Difficulty.MEDIUM
    num_bugs: int = 2   # 1-4


class ChallengeGenerateResponse(BaseModel):
    challenge_id: str
    buggy_code: str
    language: str
    num_bugs: int
    instructions: str


class ChallengeSubmitRequest(BaseModel):
    challenge_id: str
    fixed_code: str


class BugResult(BaseModel):
    bug_id: str
    fixed: bool
    explanation: str


class ChallengeSubmitResponse(BaseModel):
    score: int
    total: int
    results: list[BugResult]
    overall_feedback: str


# --- Code execution ---

class ExecuteRequest(BaseModel):
    code: str
    language: str
    stdin: Optional[str] = ""


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
