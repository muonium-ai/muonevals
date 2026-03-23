"""Track the all-time best experiment result.

best.tsv in the project root is version-controlled. When an experiment
beats the current best, this module updates the file and commits it.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sudoku.experiment import Experiment

BEST_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "best.tsv")

HEADER = "timestamp\tscore\tsteps\ttime_ms\tsolved\tconfig"


def load_best_score() -> float:
    """Load the current best score from best.tsv. Returns 0 if no file."""
    if not os.path.exists(BEST_FILE):
        return 0.0
    with open(BEST_FILE) as f:
        lines = f.readlines()
    if len(lines) < 2:
        return 0.0
    # Last line has the best
    last = lines[-1].strip()
    if not last:
        return 0.0
    parts = last.split("\t")
    return float(parts[1])


def save_best(exp: Experiment) -> str:
    """Append a new best result to best.tsv."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = (f"{ts}\t{exp.mean_score:.4f}\t{exp.mean_steps:.1f}\t"
            f"{exp.mean_time_ms:.2f}\t{exp.solved_count}/{exp.total_count}\t"
            f"{exp.description}")

    if not os.path.exists(BEST_FILE):
        with open(BEST_FILE, "w") as f:
            f.write(HEADER + "\n")

    with open(BEST_FILE, "a") as f:
        f.write(line + "\n")

    return BEST_FILE


def commit_best(exp: Experiment) -> Optional[str]:
    """Save and git-commit the new best result. Returns commit hash or None."""
    save_best(exp)

    try:
        cwd = os.path.dirname(BEST_FILE)
        subprocess.run(
            ["git", "add", "best.tsv"],
            cwd=cwd, check=True, capture_output=True,
        )
        msg = (f"New best score: {exp.mean_score:.4f} "
               f"({exp.solved_count}/{exp.total_count} solved)\n\n"
               f"Config: {exp.description}")
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=cwd, check=True, capture_output=True, text=True,
        )
        # Extract commit hash
        for line in result.stdout.splitlines():
            if line.startswith("["):
                # e.g. "[main abc1234] New best score..."
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1].rstrip("]")
        return "committed"
    except subprocess.CalledProcessError:
        return None


def check_and_commit(exp: Experiment) -> bool:
    """If exp beats the current best, save and commit. Returns True if committed."""
    current_best = load_best_score()
    if exp.mean_score > current_best:
        commit_best(exp)
        return True
    return False
