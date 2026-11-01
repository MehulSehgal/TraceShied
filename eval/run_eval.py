"""System vs single-message baseline. Usage: python eval/run_eval.py [dataset.jsonl] [--split test]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sklearn.metrics import confusion_matrix, precision_score, recall_score  # noqa: E402

from aiml.baseline import baseline_flags  # noqa: E402
from aiml.engine import analyze_conversation, load_kb  # noqa: E402

path = next((a for a in sys.argv[1:] if a.endswith(".jsonl")), "eval/dataset.sample.jsonl")
split = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else None
rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
rows = [r for r in rows if not split or r["split"] == split]
kb = load_kb()
y = [int(r["label"] == "harassment_pattern") for r in rows]
sys_p = [int(analyze_conversation(r["messages"], kb=kb)["level"] in ("High", "Elevated")) for r in rows]
base_p = [int(baseline_flags(r["messages"])) for r in rows]
for name, p in (("baseline (Detoxify or lexicon)", base_p), ("TraceShield", sys_p)):
    print(f"{name}: precision={precision_score(y, p, zero_division=0):.2f} "
          f"recall={recall_score(y, p, zero_division=0):.2f} confusion={confusion_matrix(y, p, labels=[0, 1]).tolist()}")
for r, s in zip(rows, sys_p):
    if s != int(r["label"] == "harassment_pattern"):
        print("system miss:", r["id"])
print(f"n={len(rows)} (sample data: build 100+ labeled conversations, hold out a test split, report all failures)")
