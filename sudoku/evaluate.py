"""Evaluate all strategies on a puzzle and select the best."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from sudoku.solver import Grid, is_valid
from sudoku.strategies import get, list_strategies


@dataclass
class StrategyResult:
    """Result of running a single strategy on a puzzle."""

    strategy: str
    solution: Optional[Grid]
    steps: int
    time_ms: float
    score: float


def score_result(solution: Optional[Grid], steps: int, time_ms: float) -> float:
    """Compute a combined score from correctness, efficiency, and speed."""
    correct = 1.0 if solution is not None and is_valid(solution) else 0.0
    eff = 1.0 / (1.0 + steps)
    spd = 1.0 / (1.0 + time_ms)
    # Correctness dominates: 60% correctness, 20% efficiency, 20% speed
    return 0.6 * correct + 0.2 * eff + 0.2 * spd


def evaluate_strategy(strategy_name: str, grid: Grid) -> StrategyResult:
    """Run a single strategy on a grid and return the result."""
    solver = get(strategy_name)
    start = time.perf_counter()
    solution, steps = solver(grid)
    elapsed_ms = (time.perf_counter() - start) * 1000
    sc = score_result(solution, steps, elapsed_ms)
    return StrategyResult(
        strategy=strategy_name,
        solution=solution,
        steps=steps,
        time_ms=elapsed_ms,
        score=sc,
    )


def evaluate_all(grid: Grid, strategies: Optional[List[str]] = None) -> List[StrategyResult]:
    """Evaluate all (or specified) strategies on a grid, sorted best-first."""
    if strategies is None:
        strategies = list_strategies()
    results = [evaluate_strategy(name, grid) for name in strategies]
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def select_best(grid: Grid, strategies: Optional[List[str]] = None) -> StrategyResult:
    """Run all strategies and return the best one."""
    results = evaluate_all(grid, strategies)
    return results[0]
