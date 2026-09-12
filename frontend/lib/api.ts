export type SocraticStage =
  | "orientation"
  | "localization"
  | "observation"
  | "naming"
  | "explain";

/** The four evaluation outcomes, plus terminal. Each renders differently. */
export type Branch =
  | "advance"
  | "counter_example"
  | "nudge"
  | "descend"
  | "terminate";

export const STAGE_ORDER: SocraticStage[] = [
  "orientation",
  "localization",
  "observation",
  "naming",
  "explain",
];

export const STAGE_LABEL: Record<SocraticStage, string> = {
  orientation: "Orientation",
  localization: "Localization",
  observation: "Observation",
  naming: "Naming",
  explain: "Explain",
};

export interface DiagnoseResponse {
  session_id: string;
  first_message: string;
  current_stage: SocraticStage;
  stage_index: number;
  total_stages: number;
  bug_type: string | null;
}

export interface RespondResponse {
  message: string;
  question: string | null;
  current_stage: SocraticStage;
  stage_index: number;
  total_stages: number;
  is_complete: boolean;
  summary: string | null;
  answer_correct: boolean;
  reasoning_correct: boolean;
  is_guessing: boolean;
  branch: Branch;
  descents: number;
  attempt: number; // capped at 3, then the tutor descends
  said_i_dont_know: boolean;
  run_this: string | null;
}

/* --- Quiz: the "prove it stuck" step, on the session's own concept --- */

export interface MCOption {
  label: string; // "A" | "B" | "C" | "D"
  text: string;
}

export interface MCQuestion {
  id: string;
  prompt: string;
  options: MCOption[];
  // NOTE: the answer and explanation ship with the question, so both are
  // readable in devtools. Fine for self-checking, not for grading.
  correct_label: string;
  explanation: string;
}

export interface QuizGenerateResponse {
  quiz_id: string;
  quiz_type: "mc" | "code_fix";
  mc_questions: MCQuestion[] | null;
  code_fix_questions: unknown[] | null;
}

export interface ExecuteResponse {
  stdout: string;
  stderr: string;
  exit_code: number;
}

export { ApiError, BASE, post } from "@/services/httpClient";
export { diagnose, respond } from "@/services/tutorService";
export { generateQuiz } from "@/services/quizService";
export { execute } from "@/services/executeService";
