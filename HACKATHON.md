# LLM Science Exam — Hackathon Guide

## Overview

You are given a set of difficult science questions, each with five answer choices (A–E).
Your goal is to engineer a prompt that makes a local LLM answer as many questions correctly as possible.

**No model training. No external APIs. Prompt engineering only.**

---

## What You Receive

```
your-project/
├── solution.py                    ← Only file you edit
├── data/
│   ├── test_without_answers.csv   ← 50 questions (no answers — this is your test set)
│   └── sample_submission.csv      ← Shows the required submission format
└── HACKATHON.md                   ← This file
```

---

## Rules

| Rule | Detail |
|------|--------|
| **Allowed model** | `qwen2.5:7b` via Ollama only |
| **What you may change** | Only the `prompt` variable inside `solution.py` |
| **What you may NOT change** | `MODEL`, API call logic, any other code |
| **Submission** | One `submission.csv` file per team |
| **Scoring metric** | MAP@3 (Mean Average Precision @ 3) |

---

## Setup

### Step 1 — Install Ollama

Download from [ollama.com](https://ollama.com) and install.

```bash
ollama serve            # keep this running in a separate terminal tab
ollama pull qwen2.5:7b  # one-time download (~4.7 GB)
ollama list             # verify: should show qwen2.5:7b
```

### Step 2 — Install Python dependencies

```bash
pip install pandas requests
```

---

## The Task

Each row in `test_without_answers.csv` looks like this:

| Column | Description |
|--------|-------------|
| `id` | Unique question identifier |
| `prompt` | The science question |
| `A` `B` `C` `D` `E` | Five answer choices |

Your model must output a **ranked list** of the five choices.
Only the **top 3 matter** for scoring (MAP@3).

---

## How to Participate

### Step 1 — Open `solution.py` and find the `prompt` variable

```python
# =============================================================================
#  PROMPT  ← Students: this is where your optimized prompt goes.
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
```

This is the **only thing you change**. Keep the `{question}`, `{A}`, `{B}`, `{C}`, `{D}`, `{E}`
placeholders exactly as-is — they are filled in automatically for every question.

### Step 2 — Run inference to generate your submission

```bash
python solution.py
```

This reads `data/test_without_answers.csv`, runs the model on every question using your prompt, and writes `submission.csv`.

```
Loaded 50 questions. Running inference with qwen2.5:7b ...
  [20/50] last answer: C
  [40/50] last answer: B
  [50/50] last answer: D

Done! Submission saved to submission.csv
Submit this file to the hackathon organiser for scoring.
```

### Step 3 — Submit `submission.csv`

Send `submission.csv` to your hackathon organiser. That is your final answer.

---

## Submission Format

Your `submission.csv` must have exactly two columns:

```
id,prediction
176,C A B D E
181,A B C D E
89,D A B C E
...
```

- **`id`**: the question id (must match `test_without_answers.csv`)
- **`prediction`**: five letters separated by spaces, ranked from most to least likely

The first letter is your top answer. If it is correct, you score 1.0.
If only your second letter is correct, you score 0.5. Third letter correct: 0.33.

`solution.py` generates this format automatically — you do not need to format it yourself.

See `data/sample_submission.csv` for a working example of the format.

---

## Scoring (MAP@3)

| Position of correct answer | Points |
|---------------------------|--------|
| 1st (top pick) | 1.00 |
| 2nd | 0.50 |
| 3rd | 0.33 |
| 4th or 5th | 0.00 |

Your final score is the **average** of these per-question scores across all 50 questions.

A baseline prompt (no engineering) scores approximately **0.84 MAP@3**.
Your goal is to exceed this.

---

## Prompt Engineering Tips

You can change anything about the instruction text in `prompt`. Ideas to try:

**Role definition**
```python
prompt = "You are a physics professor with 20 years of research experience..."
```

**Elimination strategy**
```python
prompt = "...First eliminate answers that are clearly wrong. Then pick the best remaining option..."
```

**Chain of thought**
```python
prompt = "...Think step by step before answering. End your response with: Answer: [letter]"
```
> Note: if you add reasoning, update `parse_answer` logic or keep the output format strict.

**Output format constraint**
```python
prompt = "...Reply with ONLY a single capital letter. No explanation. No punctuation."
```

**Few-shot examples**  
Embed 2–3 examples directly in the prompt string:
```python
prompt = """
Example 1:
Question: What is the SI unit of electric current?
A) Volt  B) Ohm  C) Ampere  D) Watt  E) Tesla
Answer: C

Now answer this question:
Question: {question}
...
"""
```

---

## Advanced: DSPy Automated Optimization

[DSPy](https://github.com/stanfordnlp/dspy) can automatically search for a better prompt.

```bash
pip install dspy
```

After optimization, DSPy saves a JSON file. Open it and find the `"instructions"` field:

```json
{
  "predict": {
    "signature": {
      "instructions": "Optimized instruction text here..."
    }
  }
}
```

Copy that value into the `prompt` variable in `solution.py` (keeping the `{question}`, `{A}`–`{E}` placeholders).

If you save your DSPy output as `dspy_prompt.json` in the project root, `solution.py` will auto-load it.

---

## FAQ

**Q: Can I change the model?**  
No. The model is fixed at `qwen2.5:7b`. Changing it will result in disqualification.

**Q: Can I change the scoring code?**  
No. `evaluate.py` is run by the organiser, not by you.

**Q: What if my submission has fewer than 50 rows?**  
Missing questions are scored as 0. Always check that `submission.csv` has all 50 IDs.

**Q: Can I submit multiple times?**  
Ask your organiser. Typically only the final submission counts.

**Q: The model is slow — is that normal?**  
Yes. A 7B model on a laptop processes 1–2 questions per minute. The full 50-question run takes ~30–50 minutes. Start early.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `ConnectionError` / `Cannot connect` | Run `ollama serve` in a separate terminal |
| `404 Not Found` | Run `ollama pull qwen2.5:7b` |
| `test_without_answers.csv not found` | Make sure the `data/` folder is in your project directory |
| Model always outputs "A" | Check Ollama is running and the model is fully downloaded |
