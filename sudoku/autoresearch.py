"""Autoresearch improvement loop for Sudoku strategies."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from sudoku.solver import Grid, is_valid
from sudoku.strategies import get, list_strategies
from sudoku.evaluate import evaluate_strategy, evaluate_all, select_best, StrategyResult


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
) -> AutoresearchResult:
    """Run the autoresearch improvement loop.

    Each round evaluates a strategy variant on the puzzle, tracks
    scores, and identifies the best performer across all rounds.

    Args:
        grid: 9x9 Sudoku grid with 0 for empty cells.
        rounds: Number of improvement rounds.
        strategies: Strategy names to explore. Defaults to all registered.
        seed: Random seed for reproducibility.

    Returns:
        AutoresearchResult with per-round data and the best strategy.
    """
    if seed is not None:
        random.seed(seed)
    if strategies is None:
        strategies = list_strategies()

    result = AutoresearchResult()

    # Round 0: evaluate all and pick the baseline best
    best = select_best(grid, strategies)
    result.rounds.append(Round(
        round_num=0,
        strategy=best.strategy,
        score=best.score,
        steps=best.steps,
        time_ms=best.time_ms,
    ))
    result.best_strategy = best.strategy
    result.best_score = best.score

    # Improvement rounds: mutate and re-evaluate
    for i in range(1, rounds):
        candidate_name = mutate(strategies)
        candidate = evaluate_strategy(candidate_name, grid)
        result.rounds.append(Round(
            round_num=i,
            strategy=candidate.strategy,
            score=candidate.score,
            steps=candidate.steps,
            time_ms=candidate.time_ms,
        ))
        if candidate.score > result.best_score:
            result.best_strategy = candidate.strategy
            result.best_score = candidate.score

    return result
