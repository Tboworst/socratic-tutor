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
    # Surfaced so the UI can show the rung counter.
    stage_index: int = 0
    total_stages: int = 5
    bug_type: Optional[str] = None


class RespondRequest(BaseModel):
    session_id: str
    user_answer: str
    # "I don't know": skips the LLM and descends. Never scored as a failure.
    i_dont_know: bool = False


class Branch(str, Enum):
    """The four outcomes, plus terminal. The UI renders each one differently."""
    ADVANCE = "advance"                  # right + right reasoning
    COUNTER_EXAMPLE = "counter_example"  # right + WRONG reasoning (key case)
    NUDGE = "nudge"                      # wrong + right reasoning
    DESCEND = "descend"                  # both wrong -> more help
    TERMINATE = "terminate"


class RespondResponse(BaseModel):
    message: str               # feedback only, no longer glued to the question
    question: Optional[str] = None   # next question, separate so the UI can lay it out
    current_stage: SocraticStage
    stage_index: int           # 0-4, for progress bar
    total_stages: int = 5
    is_complete: bool
    summary: Optional[str] = None   # Final note when session ends

    # Added: without these the four branches are invisible to the frontend.
    answer_correct: bool = False
    reasoning_correct: bool = False
    is_guessing: bool = False
    branch: Branch = Branch.DESCEND
    descents: int = 0          # times we had to give more help
    attempt: int = 1           # which try this is at the current rung
    said_i_dont_know: bool = False
    run_this: Optional[str] = None   # observation rung: snippet to execute
    correct_answer: Optional[str] = None  # revealed when session is complete


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
