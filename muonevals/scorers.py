"""Built-in scorers for muonevals."""


def correctness(solution) -> float:
    """Return 1 if solution is valid, 0 otherwise."""
    return 1.0 if solution else 0.0


def efficiency(steps: int) -> float:
    """Return normalized score inversely proportional to steps taken."""
    return 1.0 / (1.0 + steps)


def speed(time_ms: float) -> float:
    """Return normalized score inversely proportional to time in milliseconds."""
    return 1.0 / (1.0 + time_ms)
