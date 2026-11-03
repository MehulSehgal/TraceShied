import json

import pytest

from eval import run_eval


def test_metrics_report_all_confusion_matrix_outcomes():
    metrics = run_eval.calculate_metrics([1, 0, 1, 0], [1, 0, 0, 1])

    assert (metrics["TP"], metrics["TN"], metrics["FP"], metrics["FN"]) == (1, 1, 1, 1)
    assert metrics["precision"] == pytest.approx(0.5)
    assert metrics["recall"] == pytest.approx(0.5)
    assert metrics["f1"] == pytest.approx(0.5)


def test_metrics_reject_different_vector_lengths():
    with pytest.raises(ValueError, match="equal lengths; got 2 and 1"):
        run_eval.calculate_metrics([1, 0], [1])


def valid_row(**updates):
    row = {
        "id": "case-1",
        "label": "harassment_pattern",
        "split": "dev",
        "messages": [{"sender": "A", "ts": "2026-10-28T18:05:00", "text": "Hi"}],
    }
    row.update(updates)
    return row


def write_rows(path, *rows):
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_read_split_keeps_development_and_test_rows_separate(tmp_path):
    dataset = tmp_path / "dataset.jsonl"
    records = [
        valid_row(id="dev-case", split="dev"),
        valid_row(id="test-case", split="test", label="benign"),
    ]
    write_rows(dataset, *records)

    assert [row["id"] for row in run_eval.read_split(dataset, "dev")] == ["dev-case"]
    assert [row["id"] for row in run_eval.read_split(dataset, "test")] == ["test-case"]


def test_read_split_rejects_invalid_label(tmp_path):
    dataset = tmp_path / "dataset.jsonl"
    write_rows(dataset, valid_row(label="unknown"))

    with pytest.raises(ValueError, match="case 'case-1'.*'label' must be"):
        run_eval.read_split(dataset, "dev")


@pytest.mark.parametrize("missing_field", ["id", "label", "split", "messages"])
def test_read_split_rejects_missing_required_conversation_field(tmp_path, missing_field):
    dataset = tmp_path / "dataset.jsonl"
    row = valid_row()
    del row[missing_field]
    write_rows(dataset, row)

    with pytest.raises(ValueError, match=f"'{missing_field}'"):
        run_eval.read_split(dataset, "dev")


def test_read_split_rejects_malformed_json_with_line_number(tmp_path):
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text('{"id":\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Line 1: invalid JSON"):
        run_eval.read_split(dataset, "dev")


def test_read_split_rejects_valid_json_that_is_not_an_object(tmp_path):
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text("[]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Line 1: expected a JSON object"):
        run_eval.read_split(dataset, "dev")


def test_read_split_rejects_duplicate_ids(tmp_path):
    dataset = tmp_path / "dataset.jsonl"
    write_rows(dataset, valid_row(), valid_row(split="test"))

    with pytest.raises(ValueError, match="Line 2, case 'case-1': duplicate id"):
        run_eval.read_split(dataset, "dev")


@pytest.mark.parametrize(
    "messages",
    [
        [],
        ["not a message object"],
        [{"sender": "A", "text": "Hi"}],
        [{"sender": "A", "ts": "not-a-timestamp", "text": "Hi"}],
        [{"sender": " ", "ts": "2026-10-28T18:05:00", "text": "Hi"}],
        [{"ts": "2026-10-28T18:05:00", "text": "Hi"}],
        [{"sender": "A", "ts": "2026-10-28T18:05:00"}],
    ],
)
def test_read_split_rejects_invalid_message_structures(tmp_path, messages):
    dataset = tmp_path / "dataset.jsonl"
    write_rows(dataset, valid_row(messages=messages))

    with pytest.raises(ValueError, match="case 'case-1'"):
        run_eval.read_split(dataset, "dev")


def test_cli_reports_missing_split(tmp_path, capsys):
    dataset = tmp_path / "dataset.jsonl"
    write_rows(dataset, valid_row(id="dev-case", split="dev"))

    with pytest.raises(SystemExit) as exc_info:
        run_eval.main([str(dataset), "--split", "test"])

    assert exc_info.value.code == 2
    assert "No evaluation samples found for split 'test'" in capsys.readouterr().err


def test_cli_reports_empty_split(tmp_path, capsys):
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text("", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        run_eval.main([str(dataset), "--split", "dev"])

    assert exc_info.value.code == 2
    assert "No evaluation samples found for split 'dev'" in capsys.readouterr().err


def test_cli_requires_explicit_split(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run_eval.main(["eval/dataset.sample.jsonl"])

    assert exc_info.value.code == 2
    assert "--split" in capsys.readouterr().err
