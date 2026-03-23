"""Karpathy-style autoresearch experiment loop for Sudoku solvers.

The core loop:
  1. Mutate one knob in the solver config (hypothesis)
  2. Evaluate on the fixed puzzle dataset (experiment)
  3. If score improved: keep the change (accept)
     If score regressed: revert to previous best (reject)
  4. Log everything to muonledger
  5. Repeat

This mirrors autoresearch's: modify train.py → run → compare val_bpb → keep/revert
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

from sudoku.config import SolverConfig, mutate_config
from sudoku.configurable_solver import SolveResult, solve_with_config
from sudoku.dataset import get_dataset
from sudoku.evaluate import score_result
from sudoku.solver import is_valid
from muonevals.ledger import EvalLedger
from sudoku.best import load_best_score, check_and_commit


@dataclass
class Experiment:
    """One experiment in the autoresearch loop."""

    experiment_id: int
    config: SolverConfig
    description: str
    mean_score: float
    mean_steps: float
    mean_time_ms: float
    solved_count: int
    total_count: int
    status: str  # "improved", "regressed", "baseline", "failed"
    wall_time_ms: float


@dataclass
class AutoresearchRun:
    """Full autoresearch run results."""

    experiments: List[Experiment] = field(default_factory=list)
    best_config: Optional[SolverConfig] = None
    best_score: float = 0.0
    ledger: Optional[EvalLedger] = None
    total_experiments: int = 0
    improvements: int = 0

    @property
    def improvement_rate(self) -> float:
        if self.total_experiments <= 1:
            return 0.0
        return self.improvements / (self.total_experiments - 1)  # exclude baseline


def evaluate_config(config: SolverConfig) -> Experiment:
    """Evaluate a config across the full dataset.

    Like running train.py for 5 minutes — one fixed evaluation budget.
    """
    dataset = get_dataset()
    start = time.perf_counter()

    scores = []
    steps_list = []
    times_list = []
    solved = 0

    for label, grid in dataset:
        result = solve_with_config(grid, config)
        sc = score_result(result.solution, result.steps, result.time_ms)
        scores.append(sc)
        steps_list.append(result.steps)
        times_list.append(result.time_ms)
        if result.solved:
            solved += 1

    wall_time = (time.perf_counter() - start) * 1000

    return Experiment(
        experiment_id=0,  # set by caller
        config=config,
        description=config.describe(),
        mean_score=sum(scores) / len(scores),
        mean_steps=sum(steps_list) / len(steps_list),
        mean_time_ms=sum(times_list) / len(times_list),
        solved_count=solved,
        total_count=len(dataset),
        status="baseline",
        wall_time_ms=wall_time,
    )


def run_experiments(
    num_experiments: int = 20,
    seed: Optional[int] = None,
    ticket_id: str = "autoresearch",
    run_date: Optional[date] = None,
) -> AutoresearchRun:
    """Run the autoresearch experiment loop.

    Args:
        num_experiments: Total number of experiments to run.
        seed: Random seed for reproducibility.
        ticket_id: Ticket ID for ledger logging.
        run_date: Date for ledger entries.

    Returns:
        AutoresearchRun with all experiments, best config, and ledger.
    """
    ledger = EvalLedger()
    run = AutoresearchRun(ledger=ledger)

    # Load all-time best from best.tsv
    all_time_best = load_best_score()

    # Experiment 0: baseline with default config
    baseline_config = SolverConfig()
    baseline = evaluate_config(baseline_config)
    baseline.experiment_id = 0
    baseline.status = "baseline"
    run.experiments.append(baseline)
    run.best_config = baseline_config
    run.best_score = baseline.mean_score
    run.total_experiments = 1

    # Check if baseline beats all-time best
    if check_and_commit(baseline):
        print(f"*** NEW ALL-TIME BEST: {baseline.mean_score:.4f} (committed to git) ***")

    # Log baseline to ledger
    ledger.log(
        ticket_id=ticket_id,
        attempt_id=0,
        score=baseline.mean_score,
        steps=int(baseline.mean_steps),
        time_ms=baseline.mean_time_ms,
        strategy=baseline.description,
        run_date=run_date,
    )

    print(f"{'#':>3}  {'Status':>10}  {'Score':>7}  {'Steps':>7}  {'Time':>8}  {'Solved':>6}  Config")
    print("-" * 90)
    print(f"{0:>3}  {'BASELINE':>10}  {baseline.mean_score:>7.4f}  {baseline.mean_steps:>7.1f}  "
          f"{baseline.mean_time_ms:>7.2f}ms  {baseline.solved_count:>2}/{baseline.total_count:<2}  "
          f"{baseline.description}")

    # Experiment loop: mutate → evaluate → keep/revert
    current_seed = seed
    for i in range(1, num_experiments):
        # Mutate the best config (hypothesis)
        candidate_config = mutate_config(run.best_config, seed=current_seed)
        if current_seed is not None:
            current_seed += 1

        # Evaluate (experiment)
        exp = evaluate_config(candidate_config)
        exp.experiment_id = i
        run.total_experiments += 1

        # Compare (accept/reject)
        if exp.mean_score > run.best_score:
            exp.status = "improved"
            run.best_config = candidate_config
            run.best_score = exp.mean_score
            run.improvements += 1
            marker = ">>>"

            # Commit to git if this beats the all-time best
            if check_and_commit(exp):
                marker = ">>> COMMITTED"
        else:
            exp.status = "regressed"
            marker = "   "

        run.experiments.append(exp)

        # Log to ledger
        ledger.log(
            ticket_id=ticket_id,
            attempt_id=i,
            score=exp.mean_score,
            steps=int(exp.mean_steps),
            time_ms=exp.mean_time_ms,
            strategy=exp.description,
            run_date=run_date,
        )

        print(f"{i:>3}  {exp.status:>10}  {exp.mean_score:>7.4f}  {exp.mean_steps:>7.1f}  "
              f"{exp.mean_time_ms:>7.2f}ms  {exp.solved_count:>2}/{exp.total_count:<2}  "
              f"{exp.description}  {marker}")

    # Auto-save ledger
    saved_path = ledger.save()
    print(f"\n{'='*90}")
    print(f"Best score: {run.best_score:.4f} ({run.improvements} improvements in "
          f"{run.total_experiments} experiments)")
    print(f"Best config: {run.best_config.describe()}")
    print(f"Ledger saved: {saved_path}")

    return run
