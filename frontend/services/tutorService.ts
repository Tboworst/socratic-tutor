/**
 * POST /api/tutor/diagnose and POST /api/tutor/respond — the ladder itself.
 * Types live in @/lib/api; this file is just the two calls.
 */

import { post } from "./httpClient";
import type { DiagnoseResponse, RespondResponse } from "@/lib/api";

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
