"""Strategy registry for Sudoku solvers."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from sudoku.solver import Grid, solve, solve_heuristic, solve_constraint

SolverFunc = Callable[[Grid], Tuple[Optional[Grid], int]]

_REGISTRY: Dict[str, SolverFunc] = {
    "backtracking": solve,
    "heuristic": solve_heuristic,
    "constraint": solve_constraint,
}


def register(name: str, solver: SolverFunc) -> None:
    """Register a new solver strategy."""
    _REGISTRY[name] = solver


def get(name: str) -> SolverFunc:
    """Get a solver by strategy name."""
    if name not in _REGISTRY:
        raise KeyError(f"Unknown strategy: {name}. Available: {list_strategies()}")
    return _REGISTRY[name]


def list_strategies() -> List[str]:
    """Return all registered strategy names."""
    return list(_REGISTRY.keys())
