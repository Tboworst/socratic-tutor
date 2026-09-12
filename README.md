# Rung — a tutor that never answers

**LILO Summer Academy Hackathon — Track 02: Leverage AI**

> Everyone is learning to make AI write their code. Nobody is learning to debug without it.

Rung is a Socratic AI code tutor. Paste in broken code, and instead of fixing it, Rung silently diagnoses the bug and then asks you up to five questions — one small step at a time — until you find it yourself. It never hands over the answer.

## Why it's different

Most AI coding tools check *what* you say. Rung checks *how you got there*, by grading the answer and the reasoning behind it separately, every turn:

| | Reasoning correct | Reasoning wrong |
|---|---|---|
| **Answer correct** | Advance to the next rung | **"Right answer, wrong reasoning"** — a counter-example, so a lucky guess doesn't pass |
| **Answer wrong** | "Good thinking, wrong conclusion" — a nudge | Descend a level for more support |

If a student's very first answer already covers everything the remaining rungs would ask, Rung detects that (`early_win` / `fully_resolved`) and jumps straight to the final report instead of marching them through questions they've already answered.

## The five rungs

1. **Orientation** — where in the code should you even be looking?
2. **Localization** — which line or expression is the actual problem?
3. **Observation** — "run this and look": a snippet Rung generates to make the bug's behavior visible
4. **Naming** — what is this kind of bug actually called?
5. **Explain** — describe the fix, in your own words

Two Socratic answers can't trap a student forever: after a few blind guesses or repeated attempts on the same rung, Rung descends and gives more support instead of stalling.

## Beyond the ladder

- **Multi-language questions** — the tutoring conversation works for Python, JavaScript, Java, and C++ starter snippets (the LLM reasons about the code directly). Live code execution (the "run this and look" rung) is Python-only for now — other languages skip that one step and continue the ladder.
- **Quiz generator** — turns the session's bug into multiple-choice or code-fix questions, so a student can check retention after the fact.
- **Challenge mode** — generates a fresh snippet with 1-4 hidden bugs for timed, interview-style practice, separate from the guided ladder.

## Stack

- **Backend** — FastAPI, provider-agnostic LLM dispatcher (`services/llm.py`) supporting Claude, OpenRouter, or a local Ollama model, in-memory sessions mirrored to `.sessions.json` so a `--reload` doesn't lose an in-progress session, and a local sandboxed-ish Python runner (`services/runner.py`) for the observation rung.
- **Frontend** — Next.js 14 (App Router) + TypeScript + Tailwind CSS, CodeMirror 6 for the editor (Python/JS/Java/C++ syntax highlighting), a conversation-thread UI that keeps the full back-and-forth visible, not just the current question.

## Running it locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then fill in the provider you want to use
uvicorn main:app --reload
```

The API listens on `http://localhost:8000`. `GET /health` should return `{"status": "ok"}`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs on `http://localhost:3000` and expects the backend at `http://localhost:8000` (see `NEXT_PUBLIC_API_URL` in `.env.local` if you need to change that — copy `.env.local.example` to `.env.local` first).

## Environment variables (`backend/.env`)

| Variable | Used when | Notes |
|---|---|---|
| `LLM_PROVIDER` | always | `claude` \| `openrouter` \| `ollama` |
| `ANTHROPIC_API_KEY`, `CLAUDE_MODEL` | `LLM_PROVIDER=claude` | default model: `claude-sonnet-5` |
| `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | `LLM_PROVIDER=openrouter` | drop any `:free` suffix to use paid capacity — free-tier models share a throttled pool and 429 under load |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | `LLM_PROVIDER=ollama` | for a fully local setup |
| `FRONTEND_URL` | always | CORS allow-origin for the frontend |

## Testing

```bash
# Backend — a lightweight self-checking script, not pytest (run it directly)
cd backend
python test_ladder.py

# Frontend
cd frontend
npm run typecheck
npm run build
```

## Project structure

```
backend/
  main.py               FastAPI app, CORS, router registration
  routers/               tutor.py (diagnose/respond), execute.py, quiz.py, challenge.py
  services/
    llm.py               provider-agnostic dispatcher (Claude / OpenRouter / Ollama)
    runner.py            local Python execution for the observation rung
  utils/prompts.py        the Socratic prompts, including the evaluator's grading rules
  models/schemas.py       shared request/response types, the 5 stages, the branch enum

frontend/
  app/page.tsx            main tutoring screen and state machine
  components/             Hero, LadderProgress, BranchBanner, Step, Quiz, CodePanel
  services/                one file per backend route (tutorService, quizService, executeService, httpClient)
  lib/                     shared types (api.ts) and starter snippets (examples.ts)
```

## Security note

`services/runner.py` runs submitted code in a plain subprocess with no sandbox — acceptable for a local hackathon demo, not for a public deployment. A real deployment would need a real sandbox (containers, or Pyodide in-browser) before accepting code from strangers.

## Team

Built in 24 hours for the LILO Summer Academy Hackathon, Track 02 — Leverage AI.
