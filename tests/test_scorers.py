"""Tests for built-in scorers."""

import pytest
from muonevals.scorers import correctness, efficiency, speed


# A valid solved 9x9 Sudoku grid for testing
VALID_GRID = [
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


def test_correctness_valid_grid():
    assert correctness(VALID_GRID) == 1.0


def test_correctness_invalid_truthy():
    """Truthy but structurally invalid inputs should score 0."""
    assert correctness([0]) == 0.0
    assert correctness(True) == 0.0
    assert correctness([1, 2, 3]) == 0.0


def test_correctness_none_and_empty():
    assert correctness(None) == 0.0
    assert correctness([]) == 0.0
    assert correctness(False) == 0.0


def test_correctness_wrong_values():
    """A 9x9 grid with wrong values should score 0."""
    bad = [row[:] for row in VALID_GRID]
    bad[0][0] = bad[0][1]  # duplicate in row
    assert correctness(bad) == 0.0


def test_efficiency_zero_steps():
    assert efficiency(0) == 1.0


def test_efficiency_decreases_with_steps():
    assert efficiency(1) == 0.5
    assert efficiency(9) == 0.1
    assert efficiency(99) == 0.01


def test_efficiency_always_positive():
    assert efficiency(1000000) > 0


def test_efficiency_negative_raises():
    with pytest.raises(ValueError):
        efficiency(-1)
    with pytest.raises(ValueError):
        efficiency(-0.5)


def test_speed_zero_time():
    assert speed(0) == 1.0


def test_speed_decreases_with_time():
    assert speed(1) == 0.5
    assert speed(9) == 0.1


def test_speed_always_positive():
    assert speed(1000000) > 0


def test_speed_negative_raises():
    with pytest.raises(ValueError):
        speed(-1)
    with pytest.raises(ValueError):
        speed(-0.5)


def test_all_scorers_return_normalized():
    for val in [correctness(VALID_GRID), correctness(None),
                efficiency(0), efficiency(100),
                speed(0), speed(100)]:
        assert 0 <= val <= 1
