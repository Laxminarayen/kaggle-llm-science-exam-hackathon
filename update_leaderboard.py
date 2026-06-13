"""
update_leaderboard.py — Called by GitHub Actions after scoring.

Usage:
    python update_leaderboard.py <team_name> '<json_result>'

Keeps only the best score per team in docs/leaderboard.json.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LEADERBOARD = Path("docs") / "leaderboard.json"

team = sys.argv[1]
result = json.loads(sys.argv[2])

lb = json.loads(LEADERBOARD.read_text())
teams = {t["team"]: t for t in lb["teams"]}

current_best = teams.get(team, {}).get("map_at_3", -1)

if result["map_at_3"] >= current_best:
    teams[team] = {
        "team": team,
        "map_at_3": result["map_at_3"],
        "accuracy": result["accuracy"],
        "correct": result["correct"],
        "total": result["total"],
        "submitted_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    print(f"New best for {team}: MAP@3 = {result['map_at_3']:.4f} (prev best: {current_best:.4f})")
else:
    print(f"No improvement for {team}: {result['map_at_3']:.4f} <= current best {current_best:.4f} — leaderboard unchanged")

lb["teams"] = sorted(teams.values(), key=lambda x: x["map_at_3"], reverse=True)
lb["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

LEADERBOARD.write_text(json.dumps(lb, indent=2))
