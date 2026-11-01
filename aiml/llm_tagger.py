"""Optional LLM labeller for messages the rules cannot classify (Gemini API).

Off by default. Enable by setting GEMINI_API_KEY and passing build_llm_tagger() to the
engine. Text is scrubbed of PII before it gets here. Output is JSON-only, temperature 0,
and cached on disk so a demo never depends on the API being up. Not tested without a key.
"""
import hashlib
import json
import os
from pathlib import Path

CACHE = Path(os.getenv("LLM_CACHE", ".cache/llm_cache.json"))
PROMPT = """You label one message from a conversation for harassment patterns.
Labels: neutral, guilt_trip, ownership, surveillance, veiled_threat, reputation_threat, explicit_threat.
Severity 0-3. Use the reference entries and nearby messages. Hinglish is common.
Return JSON only: {{"label": "...", "severity": 0, "reason": "one line"}}

Reference entries: {ref}
Nearby messages: {ctx}
Message: {msg}"""


def build_llm_tagger():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    import google.generativeai as genai
    genai.configure(api_key=key)
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    def tag(msg: str, ctx: list, ref: list):
        k = hashlib.sha256(msg.encode()).hexdigest()
        if k in cache:
            return cache[k]
        try:
            out = model.generate_content(
                PROMPT.format(ref=ref, ctx=ctx, msg=msg),
                generation_config={"temperature": 0, "response_mime_type": "application/json"})
            res = json.loads(out.text)
        except Exception:
            return None
        cache[k] = res
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False))
        return res

    return tag
