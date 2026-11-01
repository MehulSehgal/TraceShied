# TraceShield

**Trace the pattern. Shield the person.**
A recipient-side safety assistant that detects escalating harassment across a whole conversation, explains why it was flagged, and preserves evidence. Analysis is deterministic and runs locally.

> Single-message filters judge one line at a time. TraceShield reads the conversation: contact after a refusal, late-night timing, surveillance remarks, and threats.

## Repository layout

| Folder | Part | What it holds |
|---|---|---|
| `frontend/` | Frontend | Single-page web app (HTML, CSS, JS): paste or upload a chat, live-monitor demo, risk gauge, timeline, transcript, printable evidence report |
| `backend/` | Backend | FastAPI service: `/health`, `/scrub`, `/analyze`. Stateless, stores nothing |
| `aiml/` | AI/ML | Engine (PII scrub, tagger, pattern scoring, explanation), Hinglish knowledge base, optional RAG retriever, optional LLM labeller, toxicity baseline |
| `eval/` | AI/ML | Evaluation script (precision, recall, confusion matrix) against a baseline, plus a sample dataset |
| `extension/` | Client | Chrome extension (Manifest V3) that reads messages on Instagram web after explicit consent and analyzes them on-device |
| `data/` | Demo | Hero (harassment) and benign conversations |
| `tests/` | QA | pytest tests for the engine and API |

## How it works

1. **Scrub:** phone numbers and emails are masked before any AI step.
2. **Tag:** rules and a Hinglish knowledge base (`aiml/kb/patterns.json`) label each message. An optional LLM can label messages the rules miss.
3. **Score:** a deterministic rule combines five signals into a 0 to 9 score. High at 5 or more, Elevated at 3 or 4.
4. **Explain:** plain-language reasons cite exact message numbers. The LLM never produces numbers or the risk level.
5. **Preserve:** a report with the signals, flagged messages, a SHA-256 hash and a timestamp.

| Signal | Rule | Points |
|---|---|---|
| Contact after refusal | 3 or more messages after the first refusal | 2 |
| Night-time share | more than 30% of their messages between 00:00 and 04:59 | 1 |
| Escalation trend | severity slope above 0.1 | 1 |
| Surveillance remarks | any | 2 |
| Threats | any | 3 |

The weights are heuristic. Tune them on a development split only.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt pytest httpx
python -m pytest -q tests                    # engine and API tests
uvicorn backend.app.main:app --reload        # API at http://localhost:8000/docs
python -m http.server 5500 --directory frontend   # open http://localhost:5500
```

The frontend works without the backend (it has its own copy of the engine). The "Analyze with backend" panel calls the API.

Optional AI extras: `pip install -r aiml/requirements.txt`, copy `.env.example` to `.env`, and set `GEMINI_API_KEY` to enable the LLM labeller (`"use_llm": true` in `/analyze`). The LLM path has not been tested without a key.

### API example

```bash
curl -s localhost:8000/analyze -H 'Content-Type: application/json' \
  -d @<(python -c "import json;print(json.dumps({'messages':json.load(open('data/hero_conversation.json'))}))")
```

## Chrome extension

1. Open `chrome://extensions`, turn on Developer mode, click **Load unpacked**, choose `extension/`.
2. Open Instagram web and a chat. In the TraceShield popup tick the consent box and click **Enable**. Chrome asks for permission to read instagram.com.
3. A badge appears bottom right and alerts when risk rises. Pause, Revoke access and Clear data are always available.

No network calls, no server, no accounts. Messages stay in memory. See `extension/README.md` for limits (Instagram's markup changes often, and messages already on screen have no timestamps).

## Evaluation

```bash
pip install scikit-learn            # add detoxify for the real baseline
python eval/run_eval.py eval/dataset.sample.jsonl --split test
```

`eval/dataset.sample.jsonl` has 8 hand-written conversations only to show the format. It was written alongside the rules, so its scores are **not** a result. For real numbers build 100+ labeled conversations (40+ benign, 40+ Hinglish), split roughly 70/30 into development and held-out test, never tune on the test set, and report failure cases. Run the Hinglish subset with and without the knowledge base for an ablation.

## Privacy and safety

- Scrubbing happens before any AI step. The API is stateless and does not log message text.
- The extension reads only after explicit consent and the browser permission prompt.
- This is a risk assessment, not a legal verdict. It supports documentation and does not replace legal or professional advice.
- If a conversation contains threats or surveillance: keep the original messages, tell someone you trust, consider campus or local authorities and platform reporting. In India: cybercrime.gov.in and helpline 1930 (verify current details).

## Known limitations

- Tagging is rules plus a small Hinglish glossary (7 patterns). Coverage is narrow and needs a larger, hand-checked glossary.
- The role-detection in the extension relies on message position and may need adjusting.
- Heuristic weights are not validated on real data yet.

## License

MIT
