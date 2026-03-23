"""Tests for the puzzle dataset."""

from sudoku.dataset import get_dataset, get_dataset_grids, EASY_PUZZLES, MEDIUM_PUZZLES, HARD_PUZZLES
from sudoku.solver import solve_constraint


def test_dataset_has_all_difficulties():
    ds = get_dataset()
    labels = [label for label, _ in ds]
    assert any("easy" in l for l in labels)
    assert any("medium" in l for l in labels)
    assert any("hard" in l for l in labels)


def test_dataset_size():
    assert len(get_dataset()) == 6
    assert len(get_dataset_grids()) == 6


def test_all_puzzles_are_solvable():
    for label, grid in get_dataset():
        solution, steps = solve_constraint(grid)
        assert solution is not None, f"{label} is unsolvable"


def test_all_grids_are_9x9():
    for label, grid in get_dataset():
        assert len(grid) == 9, f"{label} has {len(grid)} rows"
        for row in grid:
            assert len(row) == 9, f"{label} has row with {len(row)} cols"


def test_harder_puzzles_need_more_steps():
    """Hard puzzles need more constraint propagation steps than easy ones."""
    easy_steps = sum(solve_constraint(p)[1] for p in EASY_PUZZLES) / len(EASY_PUZZLES)
    hard_steps = sum(solve_constraint(p)[1] for p in HARD_PUZZLES) / len(HARD_PUZZLES)
    assert hard_steps > easy_steps
