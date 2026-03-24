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

from sudoku.config import SolverConfig, mutate_config, random_config, explore_config
from sudoku.configurable_solver import SolveResult, solve_with_config
from sudoku.dataset import get_dataset
from sudoku.evaluate import score_result
from sudoku.solver import is_valid
from muonevals.ledger import EvalLedger
from sudoku.best import load_best, check_and_commit


SEARCH_STRATEGIES = ("exploit", "explore", "random")


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
    search_strategy: str = "exploit"  # exploit, explore, random


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


def _build_strategy_schedule(
    num_experiments: int,
    exploit_pct: float = 0.6,
    explore_pct: float = 0.2,
    random_pct: float = 0.2,
) -> List[str]:
    """Build a schedule of search strategies for each experiment slot.

    Returns a list of strategy names (exploit/explore/random) for
    experiments 1..num_experiments-1 (experiment 0 is always baseline).
    """
    # Validate percentage inputs
    for name, pct in [("exploit_pct", exploit_pct), ("explore_pct", explore_pct), ("random_pct", random_pct)]:
        if not (0.0 <= pct <= 1.0):
            raise ValueError(f"{name} must be in [0.0, 1.0], got {pct}")
    total = exploit_pct + explore_pct + random_pct
    if abs(total - 1.0) > 0.01:
        raise ValueError(f"Percentages must sum to 1.0 (got {total})")

    n = num_experiments - 1  # exclude baseline
    if n <= 0:
        return []

    n_explore = round(n * explore_pct)
    n_random = round(n * random_pct)
    n_exploit = n - n_explore - n_random

    # Guard against rounding overshoot making n_exploit negative
    if n_exploit < 0:
        overshoot = -n_exploit
        if n_explore >= n_random:
            n_explore -= overshoot
        else:
            n_random -= overshoot
        n_exploit = 0

    schedule = (
        ["exploit"] * n_exploit
        + ["explore"] * n_explore
        + ["random"] * n_random
    )

    # Interleave: spread explore/random across the run instead of clustering
    import random as rng
    rng.shuffle(schedule)
    return schedule


def run_experiments(
    num_experiments: int = 20,
    seed: Optional[int] = None,
    ticket_id: str = "autoresearch",
    run_date: Optional[date] = None,
    exploit_pct: float = 0.6,
    explore_pct: float = 0.2,
    random_pct: float = 0.2,
) -> AutoresearchRun:
    """Run the autoresearch experiment loop with three search strategies.

    Args:
        num_experiments: Total number of experiments to run.
        seed: Random seed for reproducibility.
        ticket_id: Ticket ID for ledger logging.
        run_date: Date for ledger entries.
        exploit_pct: Fraction of experiments using exploit strategy (default 60%).
        explore_pct: Fraction using explore strategy (default 20%).
        random_pct: Fraction using random strategy (default 20%).

    Returns:
        AutoresearchRun with all experiments, best config, and ledger.
    """
    import random as rng
    if seed is not None:
        rng.seed(seed)

    ledger = EvalLedger()
    run = AutoresearchRun(ledger=ledger)

    # Load all-time best score and config from best.tsv
    all_time_best, best_config = load_best()

    # Experiment 0: start from best known config (or default if first run)
    baseline_config = best_config if best_config is not None else SolverConfig()
    if best_config is not None:
        print(f"Resuming from best config: {baseline_config.describe()} (score: {all_time_best:.4f})")
    baseline = evaluate_config(baseline_config)
    baseline.experiment_id = 0
    baseline.status = "baseline"
    baseline.search_strategy = "baseline"
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
        strategy=f"[baseline] {baseline.description}",
        run_date=run_date,
    )

    print(f"{'#':>3}  {'Strategy':>8}  {'Status':>10}  {'Score':>7}  {'Steps':>7}  {'Time':>8}  {'Solved':>6}  Config")
    print("-" * 105)
    print(f"{0:>3}  {'baseline':>8}  {'BASELINE':>10}  {baseline.mean_score:>7.4f}  {baseline.mean_steps:>7.1f}  "
          f"{baseline.mean_time_ms:>7.2f}ms  {baseline.solved_count:>2}/{baseline.total_count:<2}  "
          f"{baseline.description}")

    # Build strategy schedule
    schedule = _build_strategy_schedule(
        num_experiments, exploit_pct, explore_pct, random_pct,
    )

    # Experiment loop: generate config per strategy → evaluate → keep/revert
    current_seed = seed
    for i in range(1, num_experiments):
        search_strat = schedule[i - 1] if i - 1 < len(schedule) else "exploit"

        # Generate candidate config based on search strategy
        if search_strat == "exploit":
            candidate_config = mutate_config(run.best_config, seed=current_seed)
        elif search_strat == "explore":
            candidate_config = explore_config(run.best_config, seed=current_seed)
        else:  # random
            candidate_config = random_config(seed=current_seed)

        if current_seed is not None:
            current_seed += 1

        # Evaluate (experiment)
        exp = evaluate_config(candidate_config)
        exp.experiment_id = i
        exp.search_strategy = search_strat
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
            strategy=f"[{search_strat}] {exp.description}",
            run_date=run_date,
        )

        print(f"{i:>3}  {search_strat:>8}  {exp.status:>10}  {exp.mean_score:>7.4f}  {exp.mean_steps:>7.1f}  "
              f"{exp.mean_time_ms:>7.2f}ms  {exp.solved_count:>2}/{exp.total_count:<2}  "
              f"{exp.description}  {marker}")

    # Auto-save ledger
    saved_path = ledger.save()
    print(f"\n{'='*105}")
    print(f"Best score: {run.best_score:.4f} ({run.improvements} improvements in "
          f"{run.total_experiments} experiments)")
    print(f"Best config: {run.best_config.describe()}")

    # Strategy breakdown
    strat_counts = {}
    strat_improvements = {}
    for exp in run.experiments[1:]:  # skip baseline
        s = exp.search_strategy
        strat_counts[s] = strat_counts.get(s, 0) + 1
        if exp.status == "improved":
            strat_improvements[s] = strat_improvements.get(s, 0) + 1
    if strat_counts:
        print(f"\nStrategy breakdown:")
        for s in SEARCH_STRATEGIES:
            count = strat_counts.get(s, 0)
            improved = strat_improvements.get(s, 0)
            if count > 0:
                print(f"  {s:>8}: {count} experiments, {improved} improvements")

    print(f"Ledger saved: {saved_path}")

    return run
