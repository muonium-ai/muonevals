"""Built-in scorers for muonevals."""


def correctness(solution) -> float:
    """Score a Sudoku grid with partial credit for incomplete solutions.

    Returns:
        1.0 for a fully valid solved grid.
        For partial/invalid grids: fraction of filled cells that have no
        constraint violations (no duplicate in their row, column, or box).
        0.0 for None, empty, or structurally invalid input.
    """
    if not solution:
        return 0.0
    # Validate structure: must be a 9x9 grid of ints
    try:
        if len(solution) != 9:
            return 0.0
        for row in solution:
            if len(row) != 9:
                return 0.0
            for val in row:
                if not isinstance(val, int):
                    return 0.0
    except TypeError:
        return 0.0

    # Count filled cells and check each for constraint violations
    filled = 0
    valid = 0
    for r in range(9):
        for c in range(9):
            val = solution[r][c]
            if val < 1 or val > 9:
                continue
            filled += 1
            if not _has_conflict(solution, r, c, val):
                valid += 1

    if filled == 0:
        return 0.0
    # Perfect solution: all 81 cells filled with no conflicts
    if filled == 81 and valid == 81:
        return 1.0
    # Partial credit: fraction of conflict-free cells out of total grid
    return valid / 81


def _has_conflict(grid, row: int, col: int, val: int) -> bool:
    """Check if val at (row, col) conflicts with any peer."""
    # Row check
    for c in range(9):
        if c != col and grid[row][c] == val:
            return True
    # Column check
    for r in range(9):
        if r != row and grid[r][col] == val:
            return True
    # Box check
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if (r, c) != (row, col) and grid[r][c] == val:
                return True
    return False


def efficiency(steps: int) -> float:
    """Return normalized score inversely proportional to steps taken.

    Steps must be non-negative. Returns a value in [0, 1].
    """
    if steps < 0:
        raise ValueError(f"steps must be non-negative, got {steps}")
    return 1.0 / (1.0 + steps)


def speed(time_ms: float) -> float:
    """Return normalized score inversely proportional to time in milliseconds.

    time_ms must be non-negative. Returns a value in [0, 1].
    """
    if time_ms < 0:
        raise ValueError(f"time_ms must be non-negative, got {time_ms}")
    return 1.0 / (1.0 + time_ms)
