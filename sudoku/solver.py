"""Backtracking Sudoku solver."""

from __future__ import annotations

from typing import List, Optional, Tuple


Grid = List[List[int]]


def is_valid(grid: Grid) -> bool:
    """Check if a completed 9x9 grid is a valid Sudoku solution."""
    if len(grid) != 9 or any(len(row) != 9 for row in grid):
        return False
    for i in range(9):
        row = [grid[i][j] for j in range(9)]
        col = [grid[j][i] for j in range(9)]
        if not _is_complete_set(row) or not _is_complete_set(col):
            return False
    for br in range(3):
        for bc in range(3):
            box = [grid[br * 3 + r][bc * 3 + c] for r in range(3) for c in range(3)]
            if not _is_complete_set(box):
                return False
    return True


def _is_complete_set(nums: List[int]) -> bool:
    return sorted(nums) == list(range(1, 10))


def _find_empty(grid: Grid) -> Optional[Tuple[int, int]]:
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                return (r, c)
    return None


def _can_place(grid: Grid, row: int, col: int, num: int) -> bool:
    if num in grid[row]:
        return False
    if any(grid[r][col] == num for r in range(9)):
        return False
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if grid[r][c] == num:
                return False
    return True


def solve(grid: Grid) -> Tuple[Optional[Grid], int]:
    """Solve a Sudoku puzzle using backtracking.

    Args:
        grid: 9x9 grid with 0 for empty cells.

    Returns:
        (solved_grid, steps) or (None, steps) if unsolvable.
    """
    # Work on a copy
    grid = [row[:] for row in grid]
    steps = [0]

    def _backtrack() -> bool:
        steps[0] += 1
        pos = _find_empty(grid)
        if pos is None:
            return True
        row, col = pos
        for num in range(1, 10):
            if _can_place(grid, row, col, num):
                grid[row][col] = num
                if _backtrack():
                    return True
                grid[row][col] = 0
        return False

    if _backtrack():
        return grid, steps[0]
    return None, steps[0]
