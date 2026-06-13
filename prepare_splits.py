"""
prepare_splits.py — Run once to create the train/eval split.

Splits data/train.csv (200 rows, answers included) into:
  data/train_examples.csv  — 150 rows  (use for few-shot examples in your prompt)
  data/eval_test.csv       — 50  rows  (held-out; used by evaluate.py for scoring)

Fixed seed ensures every student evaluates on the same 50 questions.
"""

import pandas as pd
from pathlib import Path

SEED = 42
DATA_DIR = Path("data")

df = pd.read_csv(DATA_DIR / "train.csv").sample(frac=1, random_state=SEED).reset_index(drop=True)

train_examples = df.iloc[:150]
eval_test      = df.iloc[150:]

train_examples.to_csv(DATA_DIR / "train_examples.csv", index=False)
eval_test.to_csv(DATA_DIR / "eval_test.csv", index=False)

print(f"train_examples.csv : {len(train_examples)} rows  →  data/train_examples.csv")
print(f"eval_test.csv      : {len(eval_test)} rows  →  data/eval_test.csv")
print("\nDone. Run  python evaluate.py  to score your prompt.")
