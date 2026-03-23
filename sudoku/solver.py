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


def _candidates(grid: Grid, row: int, col: int) -> List[int]:
    """Return valid candidates for a cell."""
    return [n for n in range(1, 10) if _can_place(grid, row, col, n)]


def _find_least_candidates(grid: Grid) -> Optional[Tuple[int, int, List[int]]]:
    """Find the empty cell with the fewest candidates (MRV heuristic)."""
    best = None
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                cands = _candidates(grid, r, c)
                if best is None or len(cands) < len(best[2]):
                    best = (r, c, cands)
                    if len(cands) == 0:
                        return best  # early exit, no candidates = dead end
    return best


def solve_heuristic(grid: Grid) -> Tuple[Optional[Grid], int]:
    """Solve a Sudoku puzzle using backtracking with least-candidate heuristic.

    Picks the empty cell with fewest candidates first (MRV), reducing
    the search space compared to basic backtracking.

    Args:
        grid: 9x9 grid with 0 for empty cells.

    Returns:
        (solved_grid, steps) or (None, steps) if unsolvable.
    """
    grid = [row[:] for row in grid]
    steps = [0]

    def _backtrack() -> bool:
        steps[0] += 1
        result = _find_least_candidates(grid)
        if result is None:
            return True  # no empty cells
        row, col, cands = result
        for num in cands:
            grid[row][col] = num
            if _backtrack():
                return True
            grid[row][col] = 0
        return False

    if _backtrack():
        return grid, steps[0]
    return None, steps[0]


def _peers(row: int, col: int) -> List[Tuple[int, int]]:
    """Return all peer cells (same row, col, or box) excluding (row, col)."""
    peers = set()
    for c in range(9):
        if c != col:
            peers.add((row, c))
    for r in range(9):
        if r != row:
            peers.add((r, col))
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if (r, c) != (row, col):
                peers.add((r, c))
    return list(peers)


# Pre-compute peer lists
_PEERS = [[_peers(r, c) for c in range(9)] for r in range(9)]


def _init_possible(grid: Grid) -> Optional[List[List[set]]]:
    """Initialize possible-value sets from a grid. Returns None if contradiction."""
    possible = [[set(range(1, 10)) for _ in range(9)] for _ in range(9)]
    for r in range(9):
        for c in range(9):
            if grid[r][c] != 0:
                possible[r][c] = set()
    # Eliminate based on given values
    for r in range(9):
        for c in range(9):
            if grid[r][c] != 0:
                val = grid[r][c]
                for pr, pc in _PEERS[r][c]:
                    possible[pr][pc].discard(val)
    # Check for contradictions
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0 and len(possible[r][c]) == 0:
                return None
    return possible


def _propagate(grid: Grid, possible: List[List[set]], row: int, col: int, val: int) -> bool:
    """Place val at (row, col) and propagate constraints. Returns False on contradiction."""
    grid[row][col] = val
    possible[row][col] = set()
    for pr, pc in _PEERS[row][col]:
        if val in possible[pr][pc]:
            possible[pr][pc].discard(val)
            if grid[pr][pc] == 0 and len(possible[pr][pc]) == 0:
                return False
            # Naked single: only one candidate left
            if grid[pr][pc] == 0 and len(possible[pr][pc]) == 1:
                single = next(iter(possible[pr][pc]))
                if not _propagate(grid, possible, pr, pc, single):
                    return False
    return True


def solve_constraint(grid: Grid) -> Tuple[Optional[Grid], int]:
    """Solve using constraint propagation + backtracking.

    Propagates naked singles on each placement, combined with MRV
    cell selection. Faster than plain heuristic for most puzzles.

    Args:
        grid: 9x9 grid with 0 for empty cells.

    Returns:
        (solved_grid, steps) or (None, steps) if unsolvable.
    """
    grid = [row[:] for row in grid]
    possible = _init_possible(grid)
    if possible is None:
        return None, 1
    steps = [0]

    # Propagate initial naked singles
    changed = True
    while changed:
        changed = False
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0 and len(possible[r][c]) == 1:
                    val = next(iter(possible[r][c]))
                    if not _propagate(grid, possible, r, c, val):
                        return None, 1
                    changed = True

    def _backtrack(grid: Grid, possible: List[List[set]]) -> bool:
        steps[0] += 1
        # Find MRV cell
        best_r, best_c, best_cands = -1, -1, None
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    cands = possible[r][c]
                    if len(cands) == 0:
                        return False
                    if best_cands is None or len(cands) < len(best_cands):
                        best_r, best_c, best_cands = r, c, cands
        if best_cands is None:
            return True  # solved

        for val in list(best_cands):
            # Snapshot state
            grid_snap = [row[:] for row in grid]
            poss_snap = [[cell.copy() for cell in row] for row in possible]
            if _propagate(grid, possible, best_r, best_c, val):
                if _backtrack(grid, possible):
                    return True
            # Restore state
            for r in range(9):
                for c in range(9):
                    grid[r][c] = grid_snap[r][c]
                    possible[r][c] = poss_snap[r][c]
        return False

    if _backtrack(grid, possible):
        return grid, steps[0]
    return None, steps[0]


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
