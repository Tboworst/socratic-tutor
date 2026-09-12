"""
Local code execution.

Replaces services/piston.py: the public Piston API went whitelist-only on
2026-02-15, so there was no keyless hosted runner left.

SECURITY: runs untrusted code in a subprocess with no sandbox. Fine while the
backend runs on theown machine; not fine on a public host. If this
is ever deployed, maybe move to Pyodide in the browser or a container per run.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_S = 5
MAX_OUTPUT = 4000

SUPPORTED = {"python", "py", "python3"}


class UnsupportedLanguage(Exception):
    """Raised for a language this runner cannot execute."""


def execute(code: str, language: str = "python", stdin: str = "") -> dict:
    """Run a snippet and return {stdout, stderr, exit_code}."""
    if language.lower() not in SUPPORTED:
        raise UnsupportedLanguage(language)

    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "snippet.py"
        script.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(
                # -I: no site-packages, no PYTHON* env vars, cwd off sys.path.
                [sys.executable, "-I", str(script)],
                input=stdin or "",
                capture_output=True,
                text=True,
                timeout=TIMEOUT_S,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Timed out after {TIMEOUT_S}s — infinite loop?",
                "exit_code": -1,
            }
        except OSError as e:
            return {"stdout": "", "stderr": f"Could not start Python: {e}", "exit_code": -1}

    return {
        "stdout": proc.stdout[:MAX_OUTPUT],
        "stderr": proc.stderr[:MAX_OUTPUT],
        "exit_code": proc.returncode,
    }
