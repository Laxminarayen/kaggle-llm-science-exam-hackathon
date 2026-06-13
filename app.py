"""
app.py — LLM Science Exam Hackathon — Submission & Leaderboard

Deploy: connect this repo to Streamlit Community Cloud (streamlit.io/cloud).

Secrets required (set in Streamlit Cloud dashboard):
    EVAL_ANSWERS_CSV   — CSV string: "id,answer\n0,A\n1,C\n..."
    GITHUB_TOKEN       — Fine-grained PAT with Contents: Read/Write on this repo
    GITHUB_REPO        — e.g. "Laxminarayen/kaggle-llm-science-exam-hackathon"
"""

import io
import re
import json
import base64
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timezone
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LLM Science Exam Hackathon",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stHeader"] { background: transparent; }
h1 { background: linear-gradient(135deg,#6366f1,#a78bfa);
     -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
div[data-testid="metric-container"] {
    background:#1a1d27; border:1px solid #2a2d3e;
    border-radius:10px; padding:1rem 1.2rem;
}
</style>
""", unsafe_allow_html=True)

LEADERBOARD_PATH = "docs/leaderboard.json"


# ── Answer key ────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_answer_key() -> pd.DataFrame:
    try:
        csv_text = st.secrets["EVAL_ANSWERS_CSV"]
        return pd.read_csv(io.StringIO(csv_text))[["id", "answer"]]
    except Exception:
        # Local development fallback
        local = Path("data/test_synthetic_answers.csv")
        if local.exists():
            return pd.read_csv(local)[["id", "answer"]]
        return pd.read_csv("data/eval_test.csv")[["id", "answer"]]


# ── Leaderboard persistence (GitHub API) ──────────────────────────────────────
def _gh_headers() -> dict:
    token = st.secrets.get("GITHUB_TOKEN", "")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def _gh_repo() -> str:
    return st.secrets.get("GITHUB_REPO", "Laxminarayen/kaggle-llm-science-exam-hackathon")


def fetch_leaderboard() -> dict:
    """Load leaderboard.json from the GitHub repo (always fresh)."""
    try:
        url = f"https://api.github.com/repos/{_gh_repo()}/contents/{LEADERBOARD_PATH}"
        r = requests.get(url, headers=_gh_headers(), timeout=10)
        if r.ok:
            content = base64.b64decode(r.json()["content"]).decode()
            return json.loads(content), r.json()["sha"]
    except Exception:
        pass
    # Fallback to local file
    local = Path(LEADERBOARD_PATH)
    if local.exists():
        return json.loads(local.read_text()), None
    return {"last_updated": None, "teams": []}, None


def push_leaderboard(lb: dict, sha: str | None):
    """Commit updated leaderboard.json back to the repo."""
    try:
        url = f"https://api.github.com/repos/{_gh_repo()}/contents/{LEADERBOARD_PATH}"
        body: dict = {
            "message": "chore: update leaderboard [skip ci]",
            "content": base64.b64encode(json.dumps(lb, indent=2).encode()).decode(),
        }
        if sha:
            body["sha"] = sha
        requests.put(url, headers=_gh_headers(), json=body, timeout=15)
    except Exception:
        pass
    # Also write locally so local runs stay in sync
    local = Path(LEADERBOARD_PATH)
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(json.dumps(lb, indent=2))


# ── Scoring ───────────────────────────────────────────────────────────────────
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


def score(submission_df: pd.DataFrame, answers_df: pd.DataFrame) -> dict:
    merged = answers_df.merge(submission_df, on="id", how="left")
    missing = merged["prediction"].isna().sum()
    merged["prediction"] = merged["prediction"].fillna("A B C D E")
    n = len(merged)
    preds, labels = merged["prediction"].tolist(), merged["answer"].tolist()
    correct_flags = [str(p).split()[0].upper() == str(l).upper() for p, l in zip(preds, labels)]
    correct = sum(correct_flags)
    merged["top_pick"] = merged["prediction"].apply(lambda p: str(p).split()[0].upper())
    merged["correct"] = correct_flags
    return {
        "map_at_3": round(map_at_3(preds, labels), 4),
        "accuracy": round(correct / n, 4),
        "correct": correct,
        "total": n,
        "missing": int(missing),
        "detail": merged[["id", "top_pick", "answer", "correct"]],
    }


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🔬 LLM Science Exam Hackathon")
st.markdown(
    "**Prompt engineering competition** &nbsp;·&nbsp; `qwen2.5:7b` via Ollama &nbsp;·&nbsp; "
    "MAP@3 scoring &nbsp;·&nbsp; Best score per team kept"
)
st.divider()

lb_col, sub_col = st.columns([3, 2], gap="large")

# ── Leaderboard panel ─────────────────────────────────────────────────────────
with lb_col:
    st.subheader("🏆 Leaderboard")

    lb, lb_sha = fetch_leaderboard()

    if lb.get("last_updated"):
        st.caption(f"Last updated: {lb['last_updated']}")

    if lb["teams"]:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        rows = []
        for i, t in enumerate(lb["teams"], 1):
            rows.append({
                "Rank": medals.get(i, str(i)),
                "Team": t["team"],
                "MAP@3": f"{t['map_at_3']:.4f}",
                "Accuracy": f"{t['accuracy']*100:.1f}%  ({t['correct']}/{t['total']})",
                "Submitted": t.get("submitted_at", "—"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No submissions yet — be the first! 🚀")

    if st.button("↺ Refresh leaderboard"):
        st.cache_data.clear()
        st.rerun()

# ── Submission panel ──────────────────────────────────────────────────────────
with sub_col:
    st.subheader("📤 Submit Predictions")
    st.markdown(
        "Run `python solution.py` to generate your `submission.csv`, "
        "then upload it here."
    )

    team_name = st.text_input("Team Name", placeholder="e.g. team_alpha",
                               help="Letters, numbers, underscores only.")
    uploaded = st.file_uploader("Upload submission.csv", type="csv",
                                 help="Must have columns: id, prediction")

    if st.button("Submit & Score", type="primary",
                 disabled=not (team_name and uploaded)):

        team = team_name.strip().replace(" ", "_")
        if not re.match(r"^[\w-]+$", team):
            st.error("Team name may only contain letters, numbers, _ and -.")
            st.stop()

        try:
            sub_df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
            st.stop()

        missing_cols = {"id", "prediction"} - set(sub_df.columns)
        if missing_cols:
            st.error(f"Missing columns: {missing_cols}. See sample_submission.csv.")
            st.stop()

        answers_df = load_answer_key()

        with st.spinner("Scoring…"):
            result = score(sub_df, answers_df)

        # Results
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("MAP@3", f"{result['map_at_3']:.4f}")
        m2.metric("Accuracy",
                  f"{result['accuracy']*100:.1f}%",
                  f"{result['correct']}/{result['total']} correct")

        if result["missing"]:
            st.warning(f"{result['missing']} question(s) missing from submission — scored as 0.")

        # Update leaderboard
        lb, lb_sha = fetch_leaderboard()
        teams_map = {t["team"]: t for t in lb["teams"]}
        current_best = teams_map.get(team, {}).get("map_at_3", -1)

        if result["map_at_3"] > current_best:
            teams_map[team] = {
                "team": team,
                "map_at_3": result["map_at_3"],
                "accuracy": result["accuracy"],
                "correct": result["correct"],
                "total": result["total"],
                "submitted_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            }
            lb["teams"] = sorted(teams_map.values(), key=lambda x: x["map_at_3"], reverse=True)
            lb["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            push_leaderboard(lb, lb_sha)
            st.success(f"New best score for **{team}**! Leaderboard updated. 🎉")
        elif result["map_at_3"] == current_best:
            st.info(f"Same as your current best ({current_best:.4f}) — leaderboard unchanged.")
        else:
            st.info(f"Score {result['map_at_3']:.4f} is below your best {current_best:.4f} — leaderboard unchanged.")

        # Per-question breakdown
        with st.expander("Per-question breakdown"):
            detail = result["detail"].copy()
            detail["correct"] = detail["correct"].map({True: "✓", False: "✗"})
            detail.columns = ["ID", "Your Pick", "Answer", "Result"]
            st.dataframe(detail, use_container_width=True, hide_index=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center;color:#4a5568;font-size:0.8rem'>"
    "Only your <b>best</b> score is kept &nbsp;·&nbsp; "
    "Leaderboard updates live after each submission"
    "</div>",
    unsafe_allow_html=True,
)
