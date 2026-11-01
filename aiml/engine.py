"""TraceShield engine: PII scrub, message tagging, pattern scoring, explanation.

The risk score is deterministic and readable on purpose. An LLM may help label a
single message, but it never produces the numbers or the risk level.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

KB_FILE = Path(__file__).parent / "kb" / "patterns.json"
THREATS = {"veiled_threat", "reputation_threat", "explicit_threat"}
ALLOWED = {"guilt_trip", "ownership", "surveillance", "veiled_threat", "reputation_threat", "explicit_threat"}
PHONE = re.compile(r"(\+?\d[\d\s\-]{8,}\d)")
EMAIL = re.compile(r"[\w.\-]+@[\w\-]+\.\w+")
DISCLAIMER = "This is a risk assessment, not a legal verdict."

LLMFn = Callable[[str, list, list], Optional[dict]]


def load_kb(path: Path = KB_FILE) -> list[dict]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    for r in rows:
        r["_re"] = re.compile(r["pattern"], re.I)
    return rows


def scrub_text(text: str) -> tuple[str, int]:
    """Mask emails and phone numbers. Returns (clean_text, items_masked)."""
    n = 0

    def sub(tag):
        def f(_):
            nonlocal n
            n += 1
            return tag
        return f

    return PHONE.sub(sub("[PHONE]"), EMAIL.sub(sub("[EMAIL]"), text)), n


def _ts(v) -> datetime:
    if isinstance(v, datetime):
        return v
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def guess_recipient(msgs: list[dict], kb: list[dict]) -> str:
    refusal = [k for k in kb if k["role"] == "recipient"]
    for m in msgs:
        if any(k["_re"].search(m["text"]) for k in refusal):
            return m["sender"]
    senders = list(dict.fromkeys(m["sender"] for m in msgs))
    return senders[1] if len(senders) > 1 else senders[0]


def tag_messages(msgs, recipient, kb, retriever=None, llm: Optional[LLMFn] = None):
    """Rules first (cheap, deterministic), optional LLM second for what rules miss."""
    first_ref = None
    for i, m in enumerate(msgs):
        m.update(label="neutral", severity=0, hits=[], labels=[], source="rules")
        if m["sender"] == recipient:
            for k in (k for k in kb if k["role"] == "recipient"):
                if k["_re"].search(m["text"]):
                    m.update(label="refusal", hits=[k["meaning"]], labels=["refusal"])
                    first_ref = i if first_ref is None else first_ref
                    break
            continue
        hits = [k for k in kb if k["role"] == "sender" and k["_re"].search(m["text"])]
        if hits:
            top = max(hits, key=lambda k: k["severity"])
            m.update(label=top["label"], severity=top["severity"],
                     hits=[h["meaning"] for h in hits], labels=[h["label"] for h in hits])
        elif llm:
            ctx = [x["clean"] for x in msgs[max(0, i - 2): i + 1]]
            ref = retriever.retrieve(m["clean"]) if retriever else []
            res = llm(m["clean"], ctx, ref)
            if res and res.get("label") in ALLOWED:
                m.update(label=res["label"], severity=int(res.get("severity", 1)),
                         hits=[res.get("reason", "")], labels=[res["label"]], source="llm")
    for i, m in enumerate(msgs):
        if first_ref is not None and i > first_ref and m["sender"] != recipient and m["label"] == "neutral":
            m.update(label="contact_after_refusal", severity=1)
    return first_ref


def analyze_conversation(messages: list[dict], recipient: Optional[str] = None,
                         retriever=None, llm: Optional[LLMFn] = None, kb: Optional[list] = None) -> dict:
    kb = kb or load_kb()
    msgs = sorted(({"sender": m["sender"], "ts": _ts(m["ts"]), "text": m["text"]} for m in messages),
                  key=lambda m: m["ts"])
    for i, m in enumerate(msgs, 1):
        m["id"] = i
        m["clean"], _ = scrub_text(m["text"])
    recipient = recipient or guess_recipient(msgs, kb)
    fr = tag_messages(msgs, recipient, kb, retriever, llm)

    other = [m for m in msgs if m["sender"] != recipient]
    after = [m for m in other if fr is not None and m["id"] > msgs[fr]["id"]]
    night = [m for m in other if m["ts"].hour < 5]
    night_share = len(night) / len(other) if other else 0.0
    n = len(other)
    mx = (n + 1) / 2
    my = sum(m["severity"] for m in other) / n if n else 0
    den = sum((i + 1 - mx) ** 2 for i in range(n))
    slope = sum((i + 1 - mx) * (m["severity"] - my) for i, m in enumerate(other)) / den if den else 0.0
    surv = [m["id"] for m in other if "surveillance" in m["labels"]]
    thr = [m["id"] for m in other if THREATS & set(m["labels"])]

    pts = [
        ("Contact after refusal", f"{len(after)} messages", 2 if len(after) >= 3 else 0),
        ("Night-time share", f"{round(night_share * 100)}% of their messages", 1 if night_share > 0.3 else 0),
        ("Escalation trend", f"{slope:+.2f} per message", 1 if slope > 0.1 else 0),
        ("Surveillance remarks", ", ".join(f"#{i}" for i in surv) or "none", 2 if surv else 0),
        ("Threats", ", ".join(f"#{i}" for i in thr) or "none", 3 if thr else 0),
    ]
    score = sum(p[2] for p in pts)
    level = "High" if score >= 5 else "Elevated" if score >= 3 else "Low"

    why = []
    if fr is not None:
        why.append(f"After the first refusal (message #{msgs[fr]['id']}), the other person sent {len(after)} more message(s).")
    else:
        why.append("No clear refusal was found, so contact after refusal could not be measured.")
    why.append(f"{round(night_share * 100)}% of their messages were sent between 00:00 and 04:59.")
    why.append(f"Severity rises across the conversation (trend {slope:+.2f})." if slope > 0.1
               else "Severity shows no clear upward trend.")
    if surv:
        why.append("Surveillance-type remarks in " + ", ".join(f"#{i}" for i in surv) + ".")
    if thr:
        why.append("Threats or pressure to stay silent in " + ", ".join(f"#{i}" for i in thr) + ".")
    why.append(DISCLAIMER)

    digest = hashlib.sha256(json.dumps([[m["sender"], m["ts"].isoformat(), m["text"]] for m in msgs],
                                       ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "level": level, "score": score, "recipient": recipient,
        "points": [{"signal": a, "value": b, "points": c} for a, b, c in pts],
        "messages": [{"id": m["id"], "sender": m["sender"], "ts": m["ts"].isoformat(), "text": m["text"],
                      "label": m["label"], "severity": m["severity"], "hits": m["hits"], "source": m["source"]}
                     for m in msgs],
        "flagged_ids": [m["id"] for m in msgs if m["severity"] >= 1 or m["label"] == "refusal"],
        "explanation": why,
        "preview_sent_to_ai": [m["clean"] for m in msgs],
        "integrity": {"sha256": digest, "generated_at": datetime.now(timezone.utc).isoformat()},
        "disclaimer": DISCLAIMER,
    }
