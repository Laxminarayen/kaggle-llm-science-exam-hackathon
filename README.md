# Kaggle LLM Science Exam — Hackathon Starter

A baseline solution for the [Kaggle LLM Science Exam](https://www.kaggle.com/competitions/kaggle-llm-science-exam) competition.
Your only job is **prompt engineering** — no model fine-tuning, no external APIs.

---

## Hackathon Rules

| Rule | Detail |
|------|--------|
| **Allowed model** | Qwen3 4B via Ollama only (`qwen3:4b`) |
| **What you may change** | The `prompt` variable in `solution.py` OR the `dspy_prompt.json` file |
| **What you may NOT change** | `MODEL`, API call logic, evaluation code |
| **Goal** | Maximize MAP@3 on the Kaggle leaderboard |
| **Submission** | Upload `submission.csv` to Kaggle |

---

## The Task

Given a difficult science question and five answer choices (A–E), predict the correct answer.
The competition scores submissions using **MAP@3** — your top-3 ranked predictions matter most.

**Input row (test.csv):**
```
id | prompt (question)  | A  | B  | C  | D  | E
```

**Submission row (submission.csv):**
```
id | prediction
0  | C A B D E
```
The first letter in `prediction` is your top guess.

---

## Prerequisites

### 1. Python 3.10+

```bash
python --version
```

### 2. Ollama

Download and install Ollama from [ollama.com](https://ollama.com).

Start Ollama and pull the required model:

```bash
ollama serve          # keep this running in a separate terminal
ollama pull qwen3:4b  # one-time download (~2.5 GB)
```

Verify the model is available:

```bash
ollama list   # should show qwen3:4b
```

> **404 error?** This means the model is not pulled yet. Run `ollama pull qwen3:4b` and try again.
> **Connection refused?** Ollama is not running. Run `ollama serve` first.

---

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd KAGGLE-LLM-SCIENCE-EXAM

# Install dependencies
pip install -r requirements.txt
```

---

## Download the Data

1. Go to the [competition data page](https://www.kaggle.com/competitions/kaggle-llm-science-exam/data).
2. Accept the competition rules if prompted.
3. Download `train.csv` and `test.csv`.
4. Place them in the `data/` folder:

```
data/
├── train.csv
└── test.csv
```

---

## Run the Baseline

### Evaluate locally on the training set

```bash
python evaluate.py
```

This scores your current `prompt` against `data/train.csv` and prints MAP@3.
Use this to iterate quickly **without** uploading to Kaggle every time.

### Generate a Kaggle submission

```bash
python solution.py
```

Reads `data/test.csv`, runs inference, and writes `submission.csv`.

---

## How to Improve: Prompt Engineering

There are two ways to set your prompt — pick whichever fits your workflow.

---

### Option A — Edit `prompt` directly (manual)

Open `solution.py` and find this block near the top:

```python
# =============================================================================
#  PROMPT  ← Students: this is where your optimized prompt goes.
# =============================================================================
prompt = """\
You are a science expert. Answer the multiple-choice question below by \
choosing the single best option.
...
"""
```

Replace the instruction text with your improved version. Keep the
`{question}`, `{A}`, `{B}`, `{C}`, `{D}`, `{E}` placeholders — they are
filled in automatically at runtime.

Ideas to try:
- Role/persona ("You are a physics professor with 20 years of experience...")
- Chain-of-thought ("Before answering, think step by step...")
- Elimination strategy ("First eliminate clearly wrong options, then pick the best remaining one.")
- Output format constraint ("Reply with **only** the single letter. No explanation.")

After each edit, run `python evaluate.py` to see your MAP@3.

---

### Option B — DSPy JSON auto-load (recommended for DSPy users)

When a file named `dspy_prompt.json` exists in the project root, **the code
automatically loads the `instructions` field from it and overrides `prompt`**.
You do not need to touch `solution.py` at all.

A sample `dspy_prompt.json` is already included in this repo — inspect it to
understand the expected schema before replacing it with your optimized version.

**Install DSPy:**

```bash
pip install dspy
```

**Write `dspy_optimize.py`** (you create this file — not included):

```python
import dspy
import pandas as pd
import json

# Point DSPy at your local Ollama model
lm = dspy.LM("ollama_chat/qwen3:4b", api_base="http://localhost:11434", api_key="ollama")
dspy.configure(lm=lm)

# Define the signature (input/output fields for the task)
class ScienceQA(dspy.Signature):
    """Answer a science multiple-choice question."""
    question: str = dspy.InputField()
    A: str = dspy.InputField()
    B: str = dspy.InputField()
    C: str = dspy.InputField()
    D: str = dspy.InputField()
    E: str = dspy.InputField()
    answer: str = dspy.OutputField(desc="single letter: A, B, C, D, or E")

predictor = dspy.Predict(ScienceQA)

# Load a small training slice for the optimizer
train_df = pd.read_csv("data/train.csv").head(50)
trainset = [
    dspy.Example(
        question=row["prompt"], A=row["A"], B=row["B"],
        C=row["C"], D=row["D"], E=row["E"], answer=row["answer"]
    ).with_inputs("question", "A", "B", "C", "D", "E")
    for _, row in train_df.iterrows()
]

# Define the metric
def metric(example, pred, trace=None):
    return pred.answer.strip().upper() == example.answer.strip().upper()

# Run the optimizer
optimizer = dspy.BootstrapFewShot(metric=metric, max_bootstrapped_demos=3)
optimized = optimizer.compile(predictor, trainset=trainset)

# Save to dspy_prompt.json — solution.py picks this up automatically
optimized.save("dspy_prompt.json")
print("Saved to dspy_prompt.json")
```

**Run optimization:**

```bash
python dspy_optimize.py
```

**What happens next:**

When `dspy_prompt.json` is saved, open it and find the `instructions` field:

```json
{
  "predict": {
    "signature": {
      "instructions": "Your optimized instructions are here — this is what the optimizer found."
    },
    "demos": [ ... ]
  }
}
```

The next time you run `python solution.py` or `python evaluate.py`, the code
prints `[DSPy] Loaded optimized instructions from dspy_prompt.json` and uses
those instructions automatically.

> If you want to go back to your manual `prompt`, simply delete or rename
> `dspy_prompt.json` — the code falls back to the `prompt` variable in
> `solution.py`.

---

## Submit to Kaggle

```bash
python solution.py          # generates submission.csv
```

Go to the [competition submissions page](https://www.kaggle.com/competitions/kaggle-llm-science-exam/submit) and upload `submission.csv`.

---

## Project Structure

```
KAGGLE-LLM-SCIENCE-EXAM/
├── solution.py          # Baseline inference — edit `prompt` here (Option A)
├── evaluate.py          # Local MAP@3 scorer on train.csv
├── dspy_prompt.json     # Sample DSPy JSON — replace with your optimized output (Option B)
├── dspy_optimize.py     # You create this — see README for template
├── requirements.txt     # pandas, requests
├── data/
│   ├── train.csv        # Download from Kaggle (not committed to git)
│   └── test.csv         # Download from Kaggle (not committed to git)
└── submission.csv       # Generated by solution.py (not committed to git)
```

---

## Scoring Reference

**MAP@3** (Mean Average Precision @ 3):

| Top-N correct | Score |
|---------------|-------|
| 1st place correct | 1.00 |
| 2nd place correct | 0.50 |
| 3rd place correct | 0.33 |
| None of top 3 correct | 0.00 |

A random-guess baseline scores ~0.20. Good prompt engineering can push this above 0.60 on a 3B model.

---

## Tips

- Always record your MAP@3 score before changing the prompt so you can compare.
- Change one thing at a time — role, reasoning style, or output format — and re-run `evaluate.py`.
- A clear output format constraint ("reply with only the letter") is usually the single biggest win.
- Chain-of-thought ("think step by step") can help but sometimes makes answer parsing unreliable — watch the output.
- DSPy's `BootstrapFewShot` is a good starting optimizer; `MIPROv2` is more powerful but slower.
