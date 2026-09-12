/**
 * POST /api/quiz/generate — the "prove it stuck" step, on the session's own concept.
 * Types live in @/lib/api; this file is just the call.
 */

import { post } from "./httpClient";
import type { QuizGenerateResponse } from "@/lib/api";

export function generateQuiz(code: string, sessionId: string | null) {
  return post<QuizGenerateResponse>("/api/quiz/generate", {
    code,
    language: "python",
    quiz_type: "mc",
    session_id: sessionId,
  });
}
