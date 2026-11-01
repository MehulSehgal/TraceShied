import json
from pathlib import Path

from fastapi.testclient import TestClient

from aiml.engine import analyze_conversation, scrub_text
from backend.app.main import app

D = Path(__file__).resolve().parents[1] / "data"


def load(name):
    return json.loads((D / name).read_text(encoding="utf-8"))


def test_hero_is_high():
    r = analyze_conversation(load("hero_conversation.json"))
    assert r["level"] == "High" and r["score"] == 9 and r["recipient"] == "Priya"


def test_benign_is_low():
    assert analyze_conversation(load("benign_conversation.json"))["level"] == "Low"


def test_scrub():
    t, n = scrub_text("call +91 98765 43210 or a.b@x.com")
    assert n == 2 and "[PHONE]" in t and "[EMAIL]" in t


def test_api():
    c = TestClient(app)
    assert c.get("/health").json()["ok"]
    j = c.post("/analyze", json={"messages": load("hero_conversation.json")}).json()
    assert j["level"] == "High" and len(j["integrity"]["sha256"]) == 64
