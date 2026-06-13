"""
local_eval.py — Test your prompt locally before submitting.

Run:  python local_eval.py

Runs your current `prompt` from solution.py against the 150-question
training set (which has known answers), and prints your MAP@3 score.

Use this to iterate on your prompt quickly without submitting.
When you're happy with the score, run  python solution.py  to generate
your final submission.csv.
"""

import pandas as pd
from pathlib import Path
from solution import prompt, query_model, parse_answer, build_ranked_prediction

TRAIN_PATH = Path("data") / "train_examples.csv"


def map_at_3(predictions: list, labels: list) -> float:
    total = 0.0
    for pred, label in zip(predictions, labels):
        choices = pred.split()[:3]
        hits, score = 0, 0.0
        for rank, choice in enumerate(choices, 1):
            if choice == label:
                hits += 1
                score += hits / rank
        total += score
    return total / len(predictions)


def main():
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(
            f"{TRAIN_PATH} not found.\n"
            "Make sure data/train_examples.csv is in your project folder."
        )

    df = pd.read_csv(TRAIN_PATH)
    n = len(df)
    print(f"Evaluating your prompt on {n} training questions...\n")
    print(f"{'#':<5} {'OK?':<6} {'Model':<7} {'Answer':<7} Question (truncated)")
    print("-" * 75)

    preds, labels, correct = [], [], 0

    for i, (_, row) in enumerate(df.iterrows(), 1):
        filled = prompt.format(
            question=row["prompt"],
            A=row["A"], B=row["B"], C=row["C"], D=row["D"], E=row["E"],
        )
        raw = query_model(filled)
        top = parse_answer(raw)
        ranked = build_ranked_prediction(top)

        preds.append(ranked)
        labels.append(row["answer"])
        if top == row["answer"]:
            correct += 1

        status = "✓" if top == row["answer"] else "✗"
        snippet = str(row["prompt"])[:52].replace("\n", " ")
        print(f"{i:<5} {status:<6} {top:<7} {row['answer']:<7} {snippet}...")

        # Print running score every 25 questions
        if i % 25 == 0:
            running = map_at_3(preds, labels)
            print(f"\n  ── [{i}/{n}] running MAP@3: {running:.4f} ──\n")

    accuracy = correct / n
    score = map_at_3(preds, labels)

    print("-" * 75)
    print(f"\nResults on {n}-question training set:")
    print(f"  Top-1 Accuracy : {accuracy:.4f}  ({correct}/{n} correct)")
    print(f"  MAP@3          : {score:.4f}")
    print()
    print("Happy with the score? Run  python solution.py  to generate submission.csv")


if __name__ == "__main__":
    main()
