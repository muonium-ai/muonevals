"""Eval runner for muonevals."""

from __future__ import annotations

from typing import Any, Callable, List

from muonevals.eval import Eval


def run_eval(agent: Callable[[Any], Any], dataset: List[Any], eval: Eval) -> float:
    """Run an eval across a dataset and return the mean score.

    Args:
        agent: Callable that takes a dataset item and returns output.
        dataset: List of items to evaluate.
        eval: Eval instance with a scorer.

    Returns:
        Mean score across all items (0–1).

    Raises:
        ValueError: If dataset is empty.
    """
    if not dataset:
        raise ValueError("dataset must not be empty")
    scores = []
    for item in dataset:
        output = agent(item)
        score = eval.run(output)
        scores.append(score)
    return sum(scores) / len(scores)
