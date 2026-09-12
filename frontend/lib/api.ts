/**
 * Typed client for the FastAPI backend.
 * Mirrors backend/models/schemas.py exactly. If that file changes, change this one.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  said_i_dont_know: boolean;
  run_this: string | null;
}

export interface ExecuteResponse {
  stdout: string;
  stderr: string;
  exit_code: number;
}

class ApiError extends Error {}

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      `Can't reach the tutor service at ${BASE}. Is the backend running?`,
    );
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new ApiError(
      detail ? `${res.status} — ${detail.slice(0, 200)}` : `Request failed (${res.status})`,
    );
  }
  return (await res.json()) as T;
}

export function diagnose(code: string, question: string, language = "python") {
  return post<DiagnoseResponse>("/api/tutor/diagnose", { code, language, question });
}

export function respond(sessionId: string, answer: string, iDontKnow = false) {
  return post<RespondResponse>("/api/tutor/respond", {
    session_id: sessionId,
    user_answer: answer,
    i_dont_know: iDontKnow,
  });
}

export function execute(code: string, language = "python", stdin = "") {
  return post<ExecuteResponse>("/api/execute/", { code, language, stdin });
}
