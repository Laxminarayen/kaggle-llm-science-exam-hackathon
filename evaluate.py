"""
evaluate.py — Hackathon scorer (instructor / GitHub Actions use only).

Scores a student submission against the hidden answer key.

Usage:
    python evaluate.py <submission.csv>           # human-readable
    python evaluate.py <submission.csv> --json    # machine-readable (for CI)

The answer key (data/eval_test.csv) is never shared with students.
"""

import json
import sys
import pandas as pd
from pathlib import Path

ANSWER_KEY = Path("data") / "eval_test.csv"


def map_at_3(predictions: list, labels: list) -> float:
    total = 0.0
    for pred, label in zip(predictions, labels):
        choices = str(pred).split()[:3]
        hits, score = 0, 0.0
        for rank, choice in enumerate(choices, 1):
            if choice.upper() == label.upper():
                hits += 1
                score += hits / rank
        total += score
    return total / len(predictions)


def score_submission(submission_path: Path, json_mode: bool = False) -> dict:
    if not ANSWER_KEY.exists():
        raise FileNotFoundError(
            f"Answer key not found at {ANSWER_KEY}.\n"
            "Run prepare_splits.py first, or ensure eval_test.csv is present."
        )

    # Works with either the full eval_test.csv or the slim id,answer-only file
    answers = pd.read_csv(ANSWER_KEY)[["id", "answer"]]
    submission = pd.read_csv(submission_path)

    required_cols = {"id", "prediction"}
    missing = required_cols - set(submission.columns)
    if missing:
        raise ValueError(
            f"Submission is missing columns: {missing}\n"
            f"Expected: id, prediction — see sample_submission.csv for format."
        )

    merged = answers.merge(submission, on="id", how="left")
    missing_ids = merged["prediction"].isna().sum()
    if missing_ids > 0 and not json_mode:
        print(f"WARNING: {missing_ids} question(s) missing from submission — scored as 0.")
    merged["prediction"] = merged["prediction"].fillna("A B C D E")

    n = len(merged)
    preds = merged["prediction"].tolist()
    labels = merged["answer"].tolist()

    correct_count = 0
    per_question = []
    for _, row in merged.iterrows():
        top = str(row["prediction"]).split()[0].upper()
        correct = top == str(row["answer"]).upper()
        if correct:
            correct_count += 1
        per_question.append({
            "id": int(row["id"]),
            "prediction": str(row["prediction"]),
            "answer": str(row["answer"]),
            "correct": correct,
        })

    accuracy = correct_count / n
    score = map_at_3(preds, labels)
    result = {
        "map_at_3": round(score, 4),
        "accuracy": round(accuracy, 4),
        "correct": correct_count,
        "total": n,
    }

    if json_mode:
        print(json.dumps(result))
        return result

    # Human-readable output
    print(f"\nScoring: {submission_path.name}")
    print(f"{'#':<5} {'Correct?':<10} {'Submitted':<12} {'Answer':<8} Question ID")
    print("-" * 60)
    for i, q in enumerate(per_question, 1):
        status = "✓" if q["correct"] else "✗"
        print(f"{i:<5} {status:<10} {str(q['prediction'])[:10]:<12} {q['answer']:<8} id={q['id']}")

    print("-" * 60)
    print(f"\nResults for: {submission_path.name}")
    print(f"  Questions scored : {n}")
    print(f"  Top-1 Accuracy   : {accuracy:.4f}  ({correct_count}/{n} correct)")
    print(f"  MAP@3            : {score:.4f}")
    return result


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    json_mode = "--json" in flags

    if not args:
        print(__doc__)
        raise SystemExit("Error: no submission file provided.\nUsage: python evaluate.py submission.csv")

    submission_path = Path(args[0])
    if not submission_path.exists():
        raise FileNotFoundError(f"Submission file not found: {submission_path}")

    score_submission(submission_path, json_mode=json_mode)


if __name__ == "__main__":
    main()
