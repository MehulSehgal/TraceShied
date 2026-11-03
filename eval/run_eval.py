"""Compare TraceShield with the single-message baseline on one dataset split."""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aiml.baseline import baseline_flags  # noqa: E402
from aiml.engine import analyze_conversation, load_kb  # noqa: E402


LABELS = {"harassment_pattern", "benign"}
SPLITS = {"dev", "test"}


def _validate_row(row: object, line_number: int, seen_ids: set[str]) -> dict:
    if not isinstance(row, dict):
        raise ValueError(f"Line {line_number}: expected a JSON object")

    case_id = row.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError(f"Line {line_number}: 'id' must be a non-empty string")
    if case_id in seen_ids:
        raise ValueError(f"Line {line_number}, case '{case_id}': duplicate id")
    seen_ids.add(case_id)

    label = row.get("label")
    if not isinstance(label, str) or label not in LABELS:
        raise ValueError(
            f"Line {line_number}, case '{case_id}': 'label' must be "
            "'harassment_pattern' or 'benign'"
        )

    split = row.get("split")
    if not isinstance(split, str) or split not in SPLITS:
        raise ValueError(
            f"Line {line_number}, case '{case_id}': 'split' must be 'dev' or 'test'"
        )

    messages = row.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError(
            f"Line {line_number}, case '{case_id}': 'messages' must be a non-empty list"
        )
    for message_index, message in enumerate(messages, start=1):
        if not isinstance(message, dict):
            raise ValueError(
                f"Line {line_number}, case '{case_id}', message {message_index}: "
                "expected a JSON object"
            )
        for field in ("sender", "text", "ts"):
            value = message.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Line {line_number}, case '{case_id}', message {message_index}: "
                    f"'{field}' must be a non-empty string"
                )
        try:
            datetime.fromisoformat(message["ts"].replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(
                f"Line {line_number}, case '{case_id}', message {message_index}: "
                "'ts' must be a valid ISO 8601 timestamp"
            ) from error

    return row


def read_split(path: Path, split: str) -> list[dict]:
    rows = []
    seen_ids = set()
    with path.open(encoding="utf-8") as dataset:
        for line_number, line in enumerate(dataset, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Line {line_number}: invalid JSON ({error.msg})"
                ) from error
            rows.append(_validate_row(row, line_number, seen_ids))

    selected = [row for row in rows if row.get("split") == split]
    if not selected:
        raise ValueError(f"No evaluation samples found for split '{split}' in {path}")
    return selected


def calculate_metrics(y_true: list[int], y_pred: list[int]) -> dict[str, float | int]:
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"y_true and y_pred must have equal lengths; "
            f"got {len(y_true)} and {len(y_pred)}"
        )
    true_positive = sum(actual == 1 and predicted == 1 for actual, predicted in zip(y_true, y_pred))
    true_negative = sum(actual == 0 and predicted == 0 for actual, predicted in zip(y_true, y_pred))
    false_positive = sum(actual == 0 and predicted == 1 for actual, predicted in zip(y_true, y_pred))
    false_negative = sum(actual == 1 and predicted == 0 for actual, predicted in zip(y_true, y_pred))
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0
    f1 = 2 * true_positive / (2 * true_positive + false_positive + false_negative) \
        if 2 * true_positive + false_positive + false_negative else 0
    return {
        "TP": int(true_positive),
        "TN": int(true_negative),
        "FP": int(false_positive),
        "FN": int(false_negative),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dataset",
        nargs="?",
        type=Path,
        default=Path("eval/dataset.sample.jsonl"),
        help="JSONL conversation dataset (default: eval/dataset.sample.jsonl)",
    )
    parser.add_argument("--split", required=True, choices=("dev", "test"))
    args = parser.parse_args(argv)

    try:
        rows = read_split(args.dataset, args.split)
    except ValueError as error:
        parser.error(str(error))

    kb = load_kb()
    y_true = [int(row["label"] == "harassment_pattern") for row in rows]
    system_predictions = [
        int(analyze_conversation(row["messages"], kb=kb)["level"] in ("High", "Elevated"))
        for row in rows
    ]
    baseline_predictions = [int(baseline_flags(row["messages"])) for row in rows]

    print(f"split={args.split} n={len(rows)}")
    for name, predictions in (
        ("baseline (Detoxify or lexicon)", baseline_predictions),
        ("TraceShield", system_predictions),
    ):
        metrics = calculate_metrics(y_true, predictions)
        print(
            f"{name}: TP={metrics['TP']} TN={metrics['TN']} "
            f"FP={metrics['FP']} FN={metrics['FN']} "
            f"precision={metrics['precision']:.2f} "
            f"recall={metrics['recall']:.2f} F1={metrics['f1']:.2f}"
        )
    for row, prediction in zip(rows, system_predictions):
        if prediction != int(row["label"] == "harassment_pattern"):
            print("system mismatch:", row["id"])


if __name__ == "__main__":
    main()
