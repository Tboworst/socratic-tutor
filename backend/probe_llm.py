"""
Diagnostic: dump the RAW OpenRouter response.

services/llm.py keeps only choices[0].message.content, so when that field is
null we learn nothing. This prints the entire payload -- finish_reason, any
refusal, a reasoning field, usage, or an error object.

Run it from backend/ with the venv active:   python probe_llm.py
Costs exactly one request against your daily quota.
"""
import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OPENROUTER_MODEL", "inclusionai/ling-3.0-flash-vl:free")
KEY = os.getenv("OPENROUTER_API_KEY")

if not KEY:
    raise SystemExit("OPENROUTER_API_KEY missing from .env")

print(f"model : {MODEL}")
print(f"key   : {KEY[:12]}...{KEY[-4:]}\n")

payload = {
    "model": MODEL,
    "max_tokens": 1024,
    "messages": [
        {"role": "system", "content": "Respond ONLY with valid JSON. No prose, no markdown fences."},
        {"role": "user", "content": 'Return exactly this JSON: {"bug_type": "type coercion", "ok": true}'},
    ],
}

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Socratic Tutor",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=90) as r:
        status, body = r.status, r.read().decode()
except urllib.error.HTTPError as e:
    status, body = e.code, e.read().decode()
except Exception as e:
    raise SystemExit(f"network failure: {type(e).__name__}: {e}")

print(f"HTTP {status}")
print("=" * 60)
try:
    data = json.loads(body)
    print(json.dumps(data, indent=2)[:4000])
    print("=" * 60)
    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    print("VERDICT")
    print(f"  finish_reason : {choice.get('finish_reason')!r}")
    print(f"  content       : {msg.get('content')!r}")
    print(f"  reasoning     : {str(msg.get('reasoning'))[:200]!r}")
    print(f"  refusal       : {msg.get('refusal')!r}")
    print(f"  error         : {data.get('error')!r}")
    print(f"  usage         : {data.get('usage')!r}")
except json.JSONDecodeError:
    print("body was not JSON:")
    print(body[:2000])
