"""Autoresearch improvement loop for Sudoku strategies."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, List, Optional, Tuple

from sudoku.solver import Grid, is_valid
from sudoku.strategies import get, list_strategies
from sudoku.evaluate import evaluate_strategy, evaluate_all, select_best, StrategyResult
from muonevals.ledger import EvalLedger


@dataclass
class Round:
    """One round of the improvement loop."""

    round_num: int
    strategy: str
    score: float
    steps: int
    time_ms: float


@dataclass
class AutoresearchResult:
    """Result of the full autoresearch loop."""

    rounds: List[Round] = field(default_factory=list)
    best_strategy: Optional[str] = None
    best_score: float = 0.0
    ledger: Optional[EvalLedger] = field(default=None, repr=False)

    @property
    def improved(self) -> bool:
        if len(self.rounds) < 2:
            return False
        return self.rounds[-1].score > self.rounds[0].score


def mutate(strategies: List[str]) -> str:
    """Select a strategy variant to try next.

    Mutation here means picking a different strategy from the pool.
    In a full system this would modify solver parameters.
    """
    return random.choice(strategies)


def run_autoresearch(
    grid: Grid,
    rounds: int = 10,
    strategies: Optional[List[str]] = None,
    seed: Optional[int] = None,
    ticket_id: str = "autoresearch",
    run_date: Optional[date] = None,
) -> AutoresearchResult:
    """Run the autoresearch improvement loop.

    Each round evaluates a strategy variant on the puzzle, tracks
    scores, and identifies the best performer across all rounds.
    Every round is logged as a ledger transaction via EvalLedger.

    Args:
        grid: 9x9 Sudoku grid with 0 for empty cells.
        rounds: Number of improvement rounds.
        strategies: Strategy names to explore. Defaults to all registered.
        seed: Random seed for reproducibility.
        ticket_id: Ticket ID for ledger entries.
        run_date: Date for ledger entries. Defaults to today.

    Returns:
        AutoresearchResult with per-round data, best strategy, and ledger.
    """
    if seed is not None:
        random.seed(seed)
    if strategies is None:
        strategies = list_strategies()

    ledger = EvalLedger()
    result = AutoresearchResult(ledger=ledger)

    def _log_round(round_num, strategy, score, steps, time_ms):
        result.rounds.append(Round(
            round_num=round_num,
            strategy=strategy,
            score=score,
            steps=steps,
            time_ms=time_ms,
        ))
        ledger.log(
            ticket_id=ticket_id,
            attempt_id=round_num + 1,
            score=score,
            steps=steps,
            time_ms=time_ms,
            strategy=strategy,
            run_date=run_date,
        )

    # Round 0: evaluate all and pick the baseline best
    best = select_best(grid, strategies)
    _log_round(0, best.strategy, best.score, best.steps, best.time_ms)
    result.best_strategy = best.strategy
    result.best_score = best.score

    # Improvement rounds: mutate and re-evaluate
    for i in range(1, rounds):
        candidate_name = mutate(strategies)
        candidate = evaluate_strategy(candidate_name, grid)
        _log_round(i, candidate.strategy, candidate.score, candidate.steps, candidate.time_ms)
        if candidate.score > result.best_score:
            result.best_strategy = candidate.strategy
            result.best_score = candidate.score

    return result
