"""Results table and experiment summary — like autoresearch's results.tsv.

Generates a TSV log and a human-readable summary table from experiment runs.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from sudoku.experiment import AutoresearchRun


def results_to_tsv(run: AutoresearchRun) -> str:
    """Generate a results.tsv-style output.

    Columns: experiment_id, status, score, steps, time_ms, solved, config
    """
    lines = ["id\tstrategy\tstatus\tscore\tsteps\ttime_ms\tsolved\tconfig"]
    for exp in run.experiments:
        lines.append(
            f"{exp.experiment_id}\t{exp.search_strategy}\t{exp.status}\t{exp.mean_score:.4f}\t"
            f"{exp.mean_steps:.1f}\t{exp.mean_time_ms:.2f}\t"
            f"{exp.solved_count}/{exp.total_count}\t{exp.description}"
        )
    return "\n".join(lines)


def save_results_tsv(run: AutoresearchRun, path: Optional[str] = None) -> str:
    """Save results to a TSV file.

    If no path given, saves to ledgers/<timestamp>_results.tsv.
    """
    if path is None:
        ledgers_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "ledgers"
        )
        os.makedirs(ledgers_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = os.path.join(ledgers_dir, f"{ts}_results.tsv")

    with open(path, "w") as f:
        f.write(results_to_tsv(run))
    return path


def summary_table(run: AutoresearchRun) -> str:
    """Generate a human-readable summary table.

    Shows progression from baseline → best, highlighting improvements.
    """
    lines = []
    lines.append("=" * 90)
    lines.append("AUTORESEARCH EXPERIMENT SUMMARY")
    lines.append("=" * 90)
    lines.append("")

    # Progression table
    lines.append(f"{'#':>3}  {'Strategy':>8}  {'Status':>10}  {'Score':>7}  {'Steps':>7}  "
                 f"{'Time':>8}  {'Solved':>6}  Config")
    lines.append("-" * 105)

    for exp in run.experiments:
        marker = " >>>" if exp.status == "improved" else ""
        lines.append(
            f"{exp.experiment_id:>3}  {exp.search_strategy:>8}  {exp.status:>10}  {exp.mean_score:>7.4f}  "
            f"{exp.mean_steps:>7.1f}  {exp.mean_time_ms:>7.2f}ms  "
            f"{exp.solved_count:>2}/{exp.total_count:<2}  "
            f"{exp.description}{marker}"
        )

    # Summary stats
    baseline = run.experiments[0]
    lines.append("")
    lines.append("-" * 105)
    lines.append(f"Baseline score:  {baseline.mean_score:.4f}")
    lines.append(f"Best score:      {run.best_score:.4f}")
    delta = run.best_score - baseline.mean_score
    pct = (delta / baseline.mean_score * 100) if baseline.mean_score > 0 else 0
    lines.append(f"Improvement:     {delta:+.4f} ({pct:+.1f}%)")
    lines.append(f"Experiments:     {run.total_experiments}")
    lines.append(f"Improvements:    {run.improvements}")
    lines.append(f"Improvement rate: {run.improvement_rate:.0%}")
    lines.append(f"Best config:     {run.best_config.describe()}")
    lines.append("=" * 105)

    return "\n".join(lines)
