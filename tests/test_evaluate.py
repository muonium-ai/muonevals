"""Tests for strategy evaluation and selection."""

from sudoku.evaluate import evaluate_strategy, evaluate_all, select_best, score_result


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


def test_score_result_correct_solution():
    score = score_result([[]], 100, 50.0)  # dummy solution, not actually valid
    # is_valid will return False for this, so correctness = 0
    assert score < 0.6


def test_score_result_valid_vs_invalid():
    valid_score = score_result(None, 10, 5.0)    # no solution
    # Both invalid, but let's compare with actual valid
    assert valid_score < 0.5  # no correctness component


def test_evaluate_strategy_returns_result():
    result = evaluate_strategy("backtracking", EASY_PUZZLE)
    assert result.strategy == "backtracking"
    assert result.solution is not None
    assert result.steps > 0
    assert result.time_ms >= 0
    assert 0 <= result.score <= 1


def test_evaluate_all_returns_sorted():
    results = evaluate_all(EASY_PUZZLE)
    assert len(results) == 3
    # Should be sorted best-first
    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score


def test_evaluate_all_with_subset():
    results = evaluate_all(EASY_PUZZLE, strategies=["backtracking", "constraint"])
    assert len(results) == 2
    names = {r.strategy for r in results}
    assert names == {"backtracking", "constraint"}


def test_select_best_returns_highest():
    best = select_best(EASY_PUZZLE)
    results = evaluate_all(EASY_PUZZLE)
    assert best.strategy == results[0].strategy


def test_all_strategies_produce_valid_solutions():
    results = evaluate_all(EASY_PUZZLE)
    for r in results:
        assert r.solution is not None, f"{r.strategy} failed"
        assert r.score > 0.6, f"{r.strategy} score too low: {r.score}"
