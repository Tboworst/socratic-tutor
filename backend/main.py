import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import tutor, execute, quiz, challenge
from services.llm import ProviderUnavailable

app = FastAPI(title="Socratic Tutor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000"), "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tutor.router, prefix="/api/tutor", tags=["tutor"])
app.include_router(execute.router, prefix="/api/execute", tags=["execute"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(challenge.router, prefix="/api/challenge", tags=["challenge"])


@app.exception_handler(ProviderUnavailable)
def provider_unavailable(_request: Request, exc: ProviderUnavailable):
    """A provider refusing the call is not our bug: 503 with a sentence,
    not a 500 with a traceback."""
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(Exception)
def unhandled(_request: Request, exc: Exception):
    """Catch-all so every error returns JSON with CORS headers instead of a
    plain-text traceback that the browser blocks cross-origin."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
