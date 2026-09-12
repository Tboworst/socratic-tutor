"""
RETIRED — not wired into any route. The public instance went whitelist-only on
2026-02-15; services/runner.py replaced it. Keep it if our plan is to
self-host Piston, and don't point it back at emkc.org.
"""
import httpx

PISTON_URL = "https://emkc.org/api/v2/piston"

# Map common aliases to Piston's runtime names
LANGUAGE_MAP = {
    "python": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "java": "java",
    "c": "c",
    "cpp": "c++",
    "c++": "c++",
    "go": "go",
    "rust": "rust",
    "ruby": "ruby",
    "rb": "ruby",
}


# Runtimes never change during a run. Fetching them on every execute call
# doubled our exposure to Piston's rate limit for nothing.
_runtimes_cache: list[dict] | None = None


async def get_runtimes() -> list[dict]:
    global _runtimes_cache
    if _runtimes_cache is None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{PISTON_URL}/runtimes")
            r.raise_for_status()
            _runtimes_cache = r.json()
    return _runtimes_cache


async def execute(code: str, language: str, stdin: str = "") -> dict:
    """
    Returns { stdout, stderr, exit_code }.
    Raises httpx.HTTPError on network/API failure.
    """
    lang = LANGUAGE_MAP.get(language.lower(), language.lower())

    # Fetch the latest available version for this language
    runtimes = await get_runtimes()
    version = next(
        (r["version"] for r in runtimes if r["language"] == lang),
        "*",
    )

    payload = {
        "language": lang,
        "version": version,
        "files": [{"content": code}],
        "stdin": stdin,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{PISTON_URL}/execute", json=payload)
        r.raise_for_status()
        data = r.json()

    run = data.get("run", {})
    return {
        "stdout": run.get("stdout", ""),
        "stderr": run.get("stderr", ""),
        "exit_code": run.get("code", -1),
    }
