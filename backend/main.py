import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import tutor, execute

app = FastAPI(title="Socratic Tutor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000"), "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tutor.router, prefix="/api/tutor", tags=["tutor"])
app.include_router(execute.router, prefix="/api/execute", tags=["execute"])


@app.get("/health")
def health():
    return {"status": "ok"}
