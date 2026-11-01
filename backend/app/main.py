"""TraceShield API. Stateless: nothing is stored, logged, or sent to third parties by default."""
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from aiml.engine import analyze_conversation, load_kb, scrub_text
from aiml.rag import Retriever

app = FastAPI(title="TraceShield API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"])

KB = load_kb()
_retriever = None


class Msg(BaseModel):
    sender: str
    ts: str = Field(description="ISO 8601 timestamp, e.g. 2026-10-28T18:05:00")
    text: str


class AnalyzeIn(BaseModel):
    messages: list[Msg]
    recipient: Optional[str] = None
    use_llm: bool = False


class ScrubIn(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"ok": True, "kb_entries": len(KB)}


@app.post("/scrub")
def scrub(body: ScrubIn):
    clean, n = scrub_text(body.text)
    return {"clean": clean, "masked": n}


@app.post("/analyze")
def analyze(body: AnalyzeIn):
    global _retriever
    llm = None
    if body.use_llm:
        from aiml.llm_tagger import build_llm_tagger
        llm = build_llm_tagger()
        _retriever = _retriever or Retriever(KB)
    return analyze_conversation([m.model_dump() for m in body.messages], body.recipient,
                                retriever=_retriever if llm else None, llm=llm, kb=KB)
