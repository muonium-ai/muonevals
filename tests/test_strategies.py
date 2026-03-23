"""Tests for the strategy registry."""

import pytest
from sudoku.strategies import get, list_strategies, register
from sudoku.solver import is_valid


EASY_PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


def test_list_strategies_has_all_three():
    names = list_strategies()
    assert "backtracking" in names
    assert "heuristic" in names
    assert "constraint" in names


def test_get_returns_callable():
    for name in list_strategies():
        solver = get(name)
        assert callable(solver)


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        get("nonexistent")


def test_all_strategies_solve_puzzle():
    for name in list_strategies():
        solver = get(name)
        solution, steps = solver(EASY_PUZZLE)
        assert solution is not None, f"{name} failed to solve"
        assert is_valid(solution), f"{name} produced invalid solution"


def test_register_custom_strategy():
    def dummy_solver(grid):
        return None, 0

    register("dummy", dummy_solver)
    assert "dummy" in list_strategies()
    assert get("dummy") is dummy_solver
    # Clean up
    from sudoku.strategies import _REGISTRY
    del _REGISTRY["dummy"]
