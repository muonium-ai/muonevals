"""Configurable solver that respects SolverConfig parameters.

This is the solver that autoresearch mutates — every parameter in
SolverConfig affects how this solver operates.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from sudoku.config import SolverConfig
from sudoku.solver import Grid, is_valid


@dataclass
class SolveResult:
    """Result of a configurable solve."""

    solution: Optional[Grid]
    steps: int
    time_ms: float
    config: SolverConfig
    solved: bool


def _get_candidates(grid: Grid, row: int, col: int) -> List[int]:
    """Get valid candidates for a cell."""
    used = set(grid[row])
    used.update(grid[r][col] for r in range(9))
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            used.add(grid[r][c])
    return [n for n in range(1, 10) if n not in used]


def _order_candidates(candidates: List[int], grid: Grid, row: int, col: int,
                      ordering: str) -> List[int]:
    """Order candidates according to config."""
    if ordering == "ascending":
        return sorted(candidates)
    elif ordering == "descending":
        return sorted(candidates, reverse=True)
    elif ordering == "random":
        shuffled = candidates[:]
        random.shuffle(shuffled)
        return shuffled
    elif ordering == "frequency":
        # Least-frequent values in peers go first (more constraining)
        peer_vals = []
        peer_vals.extend(grid[row])
        peer_vals.extend(grid[r][col] for r in range(9))
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                peer_vals.append(grid[r][c])
        freq: Dict[int, int] = {}
        for v in peer_vals:
            if v != 0:
                freq[v] = freq.get(v, 0) + 1
        return sorted(candidates, key=lambda c: freq.get(c, 0))
    return candidates


def _find_cell(grid: Grid, use_mrv: bool) -> Optional[Tuple[int, int, List[int]]]:
    """Find next empty cell. If MRV, pick the one with fewest candidates."""
    if not use_mrv:
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    return (r, c, _get_candidates(grid, r, c))
        return None

    best = None
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                cands = _get_candidates(grid, r, c)
                if best is None or len(cands) < len(best[2]):
                    best = (r, c, cands)
                    if len(cands) == 0:
                        return best
    return best


def _propagate_naked_singles(grid: Grid, depth: int) -> bool:
    """Propagate naked singles iteratively. Returns False on contradiction.

    depth: max iterations (0 = until convergence).
    """
    iteration = 0
    while True:
        iteration += 1
        if depth > 0 and iteration > depth:
            break
        changed = False
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    cands = _get_candidates(grid, r, c)
                    if len(cands) == 0:
                        return False  # contradiction
                    if len(cands) == 1:
                        grid[r][c] = cands[0]
                        changed = True
        if not changed:
            break
    return True


def solve_with_config(grid: Grid, config: SolverConfig) -> SolveResult:
    """Solve a Sudoku puzzle using the given configuration.

    This is the function autoresearch evaluates — different configs
    produce different step counts, times, and success rates.
    """
    grid = [row[:] for row in grid]
    steps = [0]
    start = time.perf_counter()

    # Strategy determines MRV behavior; propagation knobs are orthogonal
    effective_config = config
    if config.strategy == "backtracking":
        # Pure backtracking: no MRV (scan cells top-left to bottom-right)
        if config.mrv:
            effective_config = SolverConfig(
                strategy=config.strategy,
                use_propagation=config.use_propagation,
                propagation_depth=config.propagation_depth,
                candidate_ordering=config.candidate_ordering,
                mrv=False,
                max_steps=config.max_steps,
            )
    elif config.strategy == "heuristic":
        # Heuristic: always use MRV (pick cell with fewest candidates)
        if not config.mrv:
            effective_config = SolverConfig(
                strategy=config.strategy,
                use_propagation=config.use_propagation,
                propagation_depth=config.propagation_depth,
                candidate_ordering=config.candidate_ordering,
                mrv=True,
                max_steps=config.max_steps,
            )
    # "constraint" uses all config knobs as-is

    def _backtrack() -> bool:
        steps[0] += 1
        if effective_config.max_steps and steps[0] > effective_config.max_steps:
            return False

        # Propagate naked singles if enabled
        if effective_config.use_propagation:
            snap = [r[:] for r in grid]
            if not _propagate_naked_singles(grid, effective_config.propagation_depth):
                # Contradiction — restore and return False
                for r in range(9):
                    for c in range(9):
                        grid[r][c] = snap[r][c]
                return False

        result = _find_cell(grid, effective_config.mrv)
        if result is None:
            return True  # solved
        row, col, cands = result
        if len(cands) == 0:
            if effective_config.use_propagation:
                # Restore from before propagation
                for r in range(9):
                    for c in range(9):
                        grid[r][c] = snap[r][c]
            return False

        ordered = _order_candidates(cands, grid, row, col, effective_config.candidate_ordering)

        for val in ordered:
            # Save state before this guess
            guess_snap = [r[:] for r in grid]
            grid[row][col] = val
            if _backtrack():
                return True
            # Restore
            for r in range(9):
                for c in range(9):
                    grid[r][c] = guess_snap[r][c]

        if effective_config.use_propagation:
            # Restore from before propagation
            for r in range(9):
                for c in range(9):
                    grid[r][c] = snap[r][c]
        return False

    solved = _backtrack()
    elapsed = (time.perf_counter() - start) * 1000

    return SolveResult(
        solution=grid if solved else None,
        steps=steps[0],
        time_ms=elapsed,
        config=config,
        solved=solved,
    )
