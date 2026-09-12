/**
 * Shared POST helper for every call to the FastAPI backend.
 * One place to change the base URL, the error shape, or the fetch options.
 */

export const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function post<T>(path: string, body: unknown): Promise<T> {
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
      res.status,
    );
  }
  return (await res.json()) as T;
}
