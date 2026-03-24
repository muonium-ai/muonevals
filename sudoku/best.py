"""Track the all-time best and worst experiment results.

best.tsv and worst.tsv in the project root are version-controlled.
When an experiment beats the current best (or worst), these modules
update the files and commit them.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from sudoku.experiment import Experiment
    from sudoku.config import SolverConfig

_ROOT = os.path.dirname(os.path.dirname(__file__))
BEST_FILE = os.path.join(_ROOT, "best.tsv")
WORST_FILE = os.path.join(_ROOT, "worst.tsv")

HEADER = "timestamp\tscore\tsteps\ttime_ms\tsolved\tconfig"


def _parse_config_string(config_str: str) -> Optional["SolverConfig"]:
    """Parse a config description string back into a SolverConfig.

    e.g. 'constraint | prop=full | order=ascending | mrv=on | max=50000'
    """
    from sudoku.config import SolverConfig

    parts = [p.strip() for p in config_str.split("|")]
    if len(parts) < 5:
        return None

    config = SolverConfig()
    config.strategy = parts[0]

    for part in parts[1:]:
        if part.startswith("prop="):
            val = part.split("=", 1)[1]
            if val == "full":
                config.use_propagation = True
                config.propagation_depth = 0
            else:
                config.use_propagation = True
                config.propagation_depth = int(val)
        elif part == "no-prop":
            config.use_propagation = False
        elif part.startswith("order="):
            config.candidate_ordering = part.split("=", 1)[1]
        elif part.startswith("mrv="):
            config.mrv = part.split("=", 1)[1] == "on"
        elif part.startswith("max="):
            config.max_steps = int(part.split("=", 1)[1])

    return config


def load_best() -> Tuple[float, Optional["SolverConfig"]]:
    """Load the best score and config from best.tsv. Returns (0, None) if no file."""
    if not os.path.exists(BEST_FILE):
        return 0.0, None
    with open(BEST_FILE) as f:
        lines = f.readlines()
    if len(lines) < 2:
        return 0.0, None
    # Last line has the best
    last = lines[-1].strip()
    if not last:
        return 0.0, None
    parts = last.split("\t")
    score = float(parts[1])
    config = _parse_config_string(parts[5]) if len(parts) >= 6 else None
    return score, config


def load_best_score() -> float:
    """Load the current best score from best.tsv. Returns 0 if no file."""
    score, _ = load_best()
    return score


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
    """If exp beats the current best, save and commit. Returns True only if committed."""
    current_best = load_best_score()
    if exp.mean_score > current_best:
        result = commit_best(exp)
        return result is not None
    return False


# --- Worst tracking ---

def load_worst() -> Tuple[float, Optional["SolverConfig"]]:
    """Load the worst score and config from worst.tsv. Returns (inf, None) if no file."""
    if not os.path.exists(WORST_FILE):
        return float("inf"), None
    with open(WORST_FILE) as f:
        lines = f.readlines()
    if len(lines) < 2:
        return float("inf"), None
    last = lines[-1].strip()
    if not last:
        return float("inf"), None
    parts = last.split("\t")
    score = float(parts[1])
    config = _parse_config_string(parts[5]) if len(parts) >= 6 else None
    return score, config


def load_worst_score() -> float:
    """Load the current worst score from worst.tsv. Returns inf if no file."""
    score, _ = load_worst()
    return score


def save_worst(exp: "Experiment") -> str:
    """Append a new worst result to worst.tsv."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = (f"{ts}\t{exp.mean_score:.4f}\t{exp.mean_steps:.1f}\t"
            f"{exp.mean_time_ms:.2f}\t{exp.solved_count}/{exp.total_count}\t"
            f"{exp.description}")

    if not os.path.exists(WORST_FILE):
        with open(WORST_FILE, "w") as f:
            f.write(HEADER + "\n")

    with open(WORST_FILE, "a") as f:
        f.write(line + "\n")

    return WORST_FILE


def check_and_record_worst(exp: "Experiment") -> bool:
    """If exp is worse than the current worst, save it. Returns True if recorded."""
    current_worst = load_worst_score()
    if exp.mean_score < current_worst:
        save_worst(exp)
        return True
    return False
