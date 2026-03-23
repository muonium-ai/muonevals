"""Base Eval class for muonevals."""

from typing import Any, Callable


class Eval:
    """Run a scorer against agent output and return a normalized score (0–1)."""

    def __init__(self, scorer: Callable[[Any], float]):
        self.scorer = scorer

    def run(self, output: Any) -> float:
        score = self.scorer(output)
        if not (0 <= score <= 1):
            raise ValueError(f"Scorer must return a value between 0 and 1, got {score}")
        return score
