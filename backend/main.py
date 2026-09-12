import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import tutor, execute, quiz, challenge
from services.llm import ProviderUnavailable

_ALLOWED_ORIGINS = [os.getenv("FRONTEND_URL", "http://localhost:3000"), "http://localhost:3001"]

app = FastAPI(title="Socratic Tutor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tutor.router, prefix="/api/tutor", tags=["tutor"])
app.include_router(execute.router, prefix="/api/execute", tags=["execute"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(challenge.router, prefix="/api/challenge", tags=["challenge"])


def _cors_headers(request: Request) -> dict:
    """Exception handlers bypass CORSMiddleware, so we add the header manually."""
    origin = request.headers.get("origin", "")
    if origin in _ALLOWED_ORIGINS:
        return {"Access-Control-Allow-Origin": origin}
    return {}


@app.exception_handler(ProviderUnavailable)
def provider_unavailable(request: Request, exc: ProviderUnavailable):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
        headers=_cors_headers(request),
    )


@app.exception_handler(Exception)
def unhandled(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
        headers=_cors_headers(request),
    )


@app.get("/health")
def health():
    return {"status": "ok"}
