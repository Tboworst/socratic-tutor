import { post } from "./httpClient";

export type Difficulty = "easy" | "medium" | "hard";

export interface ChallengeGenerateResponse {
  challenge_id: string;
  buggy_code: string;
  language: string;
  num_bugs: number;
  instructions: string;
}

export function generateChallenge(
  language: string,
  difficulty: Difficulty,
  num_bugs = 1,
) {
  return post<ChallengeGenerateResponse>("/api/challenge/generate", {
    language,
    difficulty,
    num_bugs,
  });
}
