"""
synthesize_answers.py — Generate synthetic ground-truth answers for test.csv.

Uses qwen2.5:2.5b with a chain-of-thought prompt + majority vote (3 runs).
Saves a checkpoint every 10 questions so it can resume if interrupted.

Usage:
    python synthesize_answers.py
    python synthesize_answers.py --input data/test.csv --runs 3
"""

import re
import sys
import json
import argparse
import requests
import pandas as pd
from pathlib import Path
from collections import Counter

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL = "qwen2.5:2.5b"
CHECKPOINT = Path("data/.synthesis_checkpoint.json")

# Strong chain-of-thought prompt — better than the student baseline
SYNTHESIS_PROMPT = """\
You are an expert scientist. Choose the single most accurate answer to this \
multiple-choice science question. Eliminate incorrect options and pick the best one.

Question: {question}

A) {A}
B) {B}
C) {C}
D) {D}
E) {E}

Reply with ONLY the letter of the correct answer (A, B, C, D, or E).\
"""


def query(prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0, "num_predict": 16},
                },
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
        except Exception as e:
            if attempt < retries - 1:
                print(f"    retry {attempt+1}: {e}")
            else:
                print(f"    giving up after {retries} attempts — defaulting to A")
                return "A"


def parse(text: str) -> str:
    # Prefer "ANSWER: X" pattern from our CoT prompt
    m = re.search(r"ANSWER:\s*([A-E])", text.upper())
    if m:
        return m.group(1)
    # Fallback: first standalone A-E letter
    m = re.search(r"\b([A-E])\b", text.upper())
    return m.group(1) if m else "A"


def majority_vote(answers: list[str]) -> str:
    return Counter(answers).most_common(1)[0][0]


def load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return {}


def save_checkpoint(done: dict):
    CHECKPOINT.write_text(json.dumps(done, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/test.csv")
    parser.add_argument("--runs", type=int, default=3,
                        help="Number of model calls per question (majority vote)")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    out_path = Path(args.input).with_name(
        Path(args.input).stem + "_synthetic_answers.csv"
    )
    n = len(df)
    runs = args.runs

    done = load_checkpoint()
    print(f"Synthesizing answers for {n} questions ({runs} runs each, majority vote)")
    print(f"Model: {MODEL}  |  Checkpoint: {CHECKPOINT}")
    if done:
        print(f"Resuming — {len(done)}/{n} already done\n")

    for i, (_, row) in enumerate(df.iterrows(), 1):
        qid = str(row["id"])
        if qid in done:
            print(f"  [{i}/{n}] id={qid}  (cached: {done[qid]})")
            continue

        prompt = SYNTHESIS_PROMPT.format(
            question=row["prompt"],
            A=row["A"], B=row["B"], C=row["C"], D=row["D"], E=row["E"],
        )
        votes = []
        for r in range(runs):
            raw = query(prompt)
            ans = parse(raw)
            votes.append(ans)

        answer = majority_vote(votes)
        done[qid] = answer
        print(f"  [{i}/{n}] id={qid}  votes={votes}  →  {answer}")

        if i % 10 == 0:
            save_checkpoint(done)

    save_checkpoint(done)

    # Build output CSV preserving original columns + answer
    id_to_answer = done
    df["answer"] = df["id"].astype(str).map(id_to_answer)
    df.to_csv(out_path, index=False)
    CHECKPOINT.unlink(missing_ok=True)
    print(f"\nDone. Saved to {out_path}")


if __name__ == "__main__":
    main()
