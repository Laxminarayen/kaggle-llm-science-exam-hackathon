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

st.set_page_config(
    page_title="LLM Science Exam Hackathon",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

# ── Session state init ────────────────────────────────────────────────────────
for key, default in [("last_result", None), ("last_team", None), ("last_msg", None)]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Secrets helpers ───────────────────────────────────────────────────────────
def _secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return default


def _gh_headers() -> dict:
    return {
        "Authorization": f"token {_secret('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json",
    }


def _gh_repo() -> str:
    return _secret("GITHUB_REPO", "Laxminarayen/kaggle-llm-science-exam-hackathon")


# ── Answer key ────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_answer_key() -> pd.DataFrame:
    csv_text = _secret("EVAL_ANSWERS_CSV")
    if csv_text:
        return pd.read_csv(io.StringIO(csv_text))[["id", "answer"]]
    for path in ["data/test_synthetic_answers.csv", "data/eval_test.csv"]:
        p = Path(path)
        if p.exists():
            return pd.read_csv(p)[["id", "answer"]]
    st.error("Answer key not found. Set EVAL_ANSWERS_CSV in Streamlit secrets.")
    st.stop()


# ── Leaderboard ───────────────────────────────────────────────────────────────
def fetch_leaderboard() -> tuple[dict, str | None]:
    """Read leaderboard — GitHub API first, local file fallback."""
    token = _secret("GITHUB_TOKEN")
    if token:
        try:
            url = f"https://api.github.com/repos/{_gh_repo()}/contents/{LEADERBOARD_PATH}"
            r = requests.get(url, headers=_gh_headers(), timeout=10)
            if r.ok:
                data = r.json()
                return json.loads(base64.b64decode(data["content"]).decode()), data["sha"]
        except Exception:
            pass

    local = Path(LEADERBOARD_PATH)
    if local.exists():
        return json.loads(local.read_text()), None
    return {"last_updated": None, "teams": []}, None


def push_leaderboard(lb: dict, sha: str | None) -> tuple[bool, str]:
    """Write leaderboard locally and to GitHub. Returns (ok, error_msg)."""
    # Always write locally
    local = Path(LEADERBOARD_PATH)
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(json.dumps(lb, indent=2))

    token = _secret("GITHUB_TOKEN")
    if not token:
        return True, ""   # local-only mode, that's fine

    try:
        url = f"https://api.github.com/repos/{_gh_repo()}/contents/{LEADERBOARD_PATH}"
        body: dict = {
            "message": "chore: update leaderboard [skip ci]",
            "content": base64.b64encode(json.dumps(lb, indent=2).encode()).decode(),
        }
        if sha:
            body["sha"] = sha
        r = requests.put(url, headers=_gh_headers(), json=body, timeout=15)
        if r.ok:
            return True, ""
        # SHA mismatch — fetch fresh SHA and retry once
        if r.status_code == 409:
            r2 = requests.get(url, headers=_gh_headers(), timeout=10)
            if r2.ok:
                body["sha"] = r2.json()["sha"]
                r3 = requests.put(url, headers=_gh_headers(), json=body, timeout=15)
                if r3.ok:
                    return True, ""
        return False, f"GitHub {r.status_code}: {r.json().get('message', r.text)}"
    except Exception as e:
        return False, str(e)


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


def score_submission(sub_df: pd.DataFrame, answers_df: pd.DataFrame) -> dict:
    merged = answers_df.merge(sub_df, on="id", how="left")
    missing = int(merged["prediction"].isna().sum())
    merged["prediction"] = merged["prediction"].fillna("A B C D E")
    n = len(merged)
    preds = merged["prediction"].tolist()
    labels = merged["answer"].tolist()
    correct_flags = [str(p).split()[0].upper() == str(l).upper() for p, l in zip(preds, labels)]
    correct = sum(correct_flags)
    merged["top_pick"] = merged["prediction"].apply(lambda p: str(p).split()[0].upper())
    merged["correct"] = correct_flags
    return {
        "map_at_3": round(map_at_3(preds, labels), 4),
        "accuracy": round(correct / n, 4),
        "correct": correct,
        "total": n,
        "missing": missing,
        "detail": merged[["id", "top_pick", "answer", "correct"]].copy(),
    }


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🔬 LLM Science Exam Hackathon")
st.markdown(
    "**Prompt engineering competition** &nbsp;·&nbsp; `qwen2.5:2.5b` via Ollama &nbsp;·&nbsp; "
    "MAP@3 scoring &nbsp;·&nbsp; Best score per team kept"
)
st.divider()

lb_col, sub_col = st.columns([3, 2], gap="large")

# ── Leaderboard ───────────────────────────────────────────────────────────────
with lb_col:
    st.subheader("🏆 Leaderboard")
    lb, lb_sha = fetch_leaderboard()

    if lb.get("last_updated"):
        st.caption(f"Last updated: {lb['last_updated']}")

    if lb["teams"]:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        rows = [
            {
                "Rank": medals.get(i, str(i)),
                "Team": t["team"],
                "MAP@3": f"{t['map_at_3']:.4f}",
                "Accuracy": f"{t['accuracy']*100:.1f}%  ({t['correct']}/{t['total']})",
                "Submitted": t.get("submitted_at", "—"),
            }
            for i, t in enumerate(lb["teams"], 1)
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No submissions yet — be the first! 🚀")

    if st.button("↺ Refresh leaderboard"):
        st.rerun()

# ── Submission ────────────────────────────────────────────────────────────────
with sub_col:
    st.subheader("📤 Submit Predictions")
    st.markdown("Run `python solution.py` to generate `submission.csv`, then upload here.")

    team_input = st.text_input("Team Name", placeholder="e.g. team_alpha")
    uploaded = st.file_uploader("Upload submission.csv", type="csv")

    if st.button("Submit & Score", type="primary", disabled=not (team_input and uploaded)):
        team = team_input.strip().replace(" ", "_")

        if not re.match(r"^[\w-]+$", team):
            st.error("Team name: letters, numbers, _ and - only.")
        else:
            try:
                sub_df = pd.read_csv(uploaded)
            except Exception as e:
                st.error(f"Could not read CSV: {e}")
                st.stop()

            missing_cols = {"id", "prediction"} - set(sub_df.columns)
            if missing_cols:
                st.error(f"Missing columns: {missing_cols}. See sample_submission.csv.")
                st.stop()

            with st.spinner("Scoring…"):
                result = score_submission(sub_df, load_answer_key())

            # Fetch fresh leaderboard right before writing
            lb_now, sha_now = fetch_leaderboard()
            teams_map = {t["team"]: t for t in lb_now["teams"]}
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
                lb_now["teams"] = sorted(
                    teams_map.values(), key=lambda x: x["map_at_3"], reverse=True
                )
                lb_now["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                ok, err = push_leaderboard(lb_now, sha_now)
                msg = ("✅ New best score! Leaderboard updated." if ok
                       else f"⚠️ Scored but leaderboard write failed: {err}")
            elif result["map_at_3"] == current_best:
                msg = f"ℹ️ Same as your current best ({current_best:.4f}) — no change."
            else:
                msg = f"ℹ️ {result['map_at_3']:.4f} is below your best {current_best:.4f} — no change."

            # Store in session state then rerun so leaderboard refreshes
            st.session_state.last_result = result
            st.session_state.last_team = team
            st.session_state.last_msg = msg
            st.rerun()

    # Show last submission result (persists across reruns via session state)
    if st.session_state.last_result:
        result = st.session_state.last_result
        st.divider()

        msg = st.session_state.last_msg or ""
        if msg.startswith("✅"):
            st.success(msg)
        elif msg.startswith("⚠️"):
            st.warning(msg)
        else:
            st.info(msg)

        if result["missing"]:
            st.warning(f"{result['missing']} question(s) missing — scored as 0.")

        m1, m2 = st.columns(2)
        m1.metric("MAP@3", f"{result['map_at_3']:.4f}")
        m2.metric(
            "Accuracy",
            f"{result['accuracy']*100:.1f}%",
            f"{result['correct']}/{result['total']} correct",
        )

        with st.expander("Per-question breakdown"):
            detail = result["detail"].copy()
            detail["correct"] = detail["correct"].map({True: "✓", False: "✗"})
            detail.columns = ["ID", "Your Pick", "Answer", "Result"]
            st.dataframe(detail, use_container_width=True, hide_index=True)

st.divider()
st.markdown(
    "<div style='text-align:center;color:#4a5568;font-size:0.8rem'>"
    "Only your <b>best</b> score is kept &nbsp;·&nbsp; "
    "Leaderboard refreshes after every submission"
    "</div>",
    unsafe_allow_html=True,
)
