"""Built-in scorers for muonevals."""


def correctness(solution) -> float:
    """Return 1 if solution is a valid 9x9 Sudoku grid, 0 otherwise."""
    if not solution:
        return 0.0
    # Validate structure: must be a 9x9 grid of ints 1-9
    try:
        if len(solution) != 9:
            return 0.0
        for row in solution:
            if len(row) != 9:
                return 0.0
            for val in row:
                if not isinstance(val, int) or val < 1 or val > 9:
                    return 0.0
    except TypeError:
        return 0.0
    # Check Sudoku validity (rows, cols, boxes)
    for i in range(9):
        row = [solution[i][j] for j in range(9)]
        col = [solution[j][i] for j in range(9)]
        if sorted(row) != list(range(1, 10)) or sorted(col) != list(range(1, 10)):
            return 0.0
    for br in range(3):
        for bc in range(3):
            box = [solution[br * 3 + r][bc * 3 + c] for r in range(3) for c in range(3)]
            if sorted(box) != list(range(1, 10)):
                return 0.0
    return 1.0


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
