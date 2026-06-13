"""
solution.py — Kaggle LLM Science Exam baseline
Model: Qwen 3B via Ollama

Hackathon rule: only modify the `prompt` variable below.
"""

import re
import pandas as pd
import requests
from pathlib import Path

# =============================================================================
#  PROMPT  ← Students: paste your optimized prompt here.
#
#  Workflow:
#   1. Use DSPy to optimize your prompt (see README for details).
#   2. After compilation, DSPy saves a JSON file. Open it and find the
#      "instructions" field inside your predictor block.
#   3. Copy that value into this variable.
#
#  Keep the {question}, {A}, {B}, {C}, {D}, {E} placeholders exactly as-is —
#  they are filled in at runtime with each row from the test set.
# =============================================================================
prompt = """\
Question: {question}
A) {A}
B) {B}
C) {C}
D) {D}
E) {E}
Answer:\
"""

# --- Configuration -----------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"   # Hackathon rule: do not change this
DATA_DIR = Path("data")
OUTPUT_FILE = Path("submission.csv")
# -----------------------------------------------------------------------------


def query_model(filled_prompt: str) -> str:
    """Send a prompt to Ollama chat API and return the raw text response."""
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": filled_prompt}],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 64},
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def parse_answer(text: str) -> str:
    """Return the first A-E letter found in the model output, default 'A'."""
    match = re.search(r"\b([A-E])\b", text.upper())
    return match.group(1) if match else "A"


def build_ranked_prediction(top: str) -> str:
    """
    Return all five choices space-separated, with the model's pick first
    and the rest in alphabetical order (required by MAP@3 submission format).
    """
    remaining = [c for c in "ABCDE" if c != top]
    return " ".join([top] + remaining)


def run_inference(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    n = len(df)
    for i, (_, row) in enumerate(df.iterrows(), 1):
        filled = prompt.format(
            question=row["prompt"],
            A=row["A"], B=row["B"], C=row["C"], D=row["D"], E=row["E"],
        )
        raw = query_model(filled)
        top = parse_answer(raw)
        results.append({"id": row["id"], "prediction": build_ranked_prediction(top)})
        if i % 20 == 0 or i == n:
            print(f"  [{i}/{n}] last answer: {top}")
    return pd.DataFrame(results)


def main():
    test_path = DATA_DIR / "test.csv"
    if not test_path.exists():
        raise FileNotFoundError(
            f"{test_path} not found.\n"
            "Make sure data/test.csv is in your project folder.\n"
            "Contact the hackathon organiser if you are missing this file."
        )
    test_df = pd.read_csv(test_path)
    print(f"Loaded {len(test_df)} questions. Running inference with {MODEL} ...")
    submission = run_inference(test_df)
    submission.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Submission saved to {OUTPUT_FILE}")
    print(f"Submit this file to the hackathon organiser for scoring.\n")
    print(submission.head().to_string(index=False))


if __name__ == "__main__":
    main()
