"""Tests for the Sudoku solver."""

from sudoku.solver import solve, solve_heuristic, is_valid


# A known easy puzzle
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

EASY_SOLUTION = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


def test_solve_easy_puzzle():
    solution, steps = solve(EASY_PUZZLE)
    assert solution is not None
    assert solution == EASY_SOLUTION


def test_solution_is_valid():
    solution, _ = solve(EASY_PUZZLE)
    assert is_valid(solution)


def test_steps_are_positive():
    _, steps = solve(EASY_PUZZLE)
    assert steps > 0


def test_original_grid_unchanged():
    original = [row[:] for row in EASY_PUZZLE]
    solve(EASY_PUZZLE)
    assert EASY_PUZZLE == original


def test_already_solved():
    solution, steps = solve(EASY_SOLUTION)
    assert solution == EASY_SOLUTION
    assert steps == 1  # just checks, finds no empty


def test_unsolvable_puzzle():
    # Two 5s in the first row -> unsolvable
    bad = [row[:] for row in EASY_PUZZLE]
    bad[0][0] = 5
    bad[0][1] = 5
    solution, steps = solve(bad)
    assert solution is None


def test_is_valid_rejects_incomplete():
    incomplete = [row[:] for row in EASY_PUZZLE]
    assert not is_valid(incomplete)


def test_is_valid_rejects_wrong_size():
    assert not is_valid([[1, 2, 3]])
    assert not is_valid([])


# --- Heuristic solver tests ---

def test_heuristic_solves_easy_puzzle():
    solution, steps = solve_heuristic(EASY_PUZZLE)
    assert solution is not None
    assert solution == EASY_SOLUTION


def test_heuristic_solution_is_valid():
    solution, _ = solve_heuristic(EASY_PUZZLE)
    assert is_valid(solution)


def test_heuristic_fewer_steps_than_baseline():
    _, baseline_steps = solve(EASY_PUZZLE)
    _, heuristic_steps = solve_heuristic(EASY_PUZZLE)
    assert heuristic_steps < baseline_steps


def test_heuristic_unsolvable():
    bad = [row[:] for row in EASY_PUZZLE]
    bad[0][0] = 5
    bad[0][1] = 5
    solution, _ = solve_heuristic(bad)
    assert solution is None
