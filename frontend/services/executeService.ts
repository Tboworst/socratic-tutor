/**
 * POST /api/execute/ — run a snippet through the backend's local runner.
 * Type lives in @/lib/api; this file is just the call.
 */

import { post } from "./httpClient";
import type { ExecuteResponse } from "@/lib/api";

export function execute(code: string, language = "python", stdin = "") {
  return post<ExecuteResponse>("/api/execute/", { code, language, stdin });
}
