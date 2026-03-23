"""Tests for the autoresearch improvement loop."""

from sudoku.autoresearch import run_autoresearch, mutate, AutoresearchResult


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


def test_autoresearch_runs_correct_rounds():
    result = run_autoresearch(EASY_PUZZLE, rounds=5, seed=42)
    assert len(result.rounds) == 5


def test_autoresearch_has_best_strategy():
    result = run_autoresearch(EASY_PUZZLE, rounds=10, seed=42)
    assert result.best_strategy is not None
    assert result.best_strategy in ["backtracking", "heuristic", "constraint"]


def test_autoresearch_best_score_positive():
    result = run_autoresearch(EASY_PUZZLE, rounds=10, seed=42)
    assert result.best_score > 0.6  # all strategies solve this puzzle


def test_autoresearch_best_score_matches_rounds():
    result = run_autoresearch(EASY_PUZZLE, rounds=10, seed=42)
    max_round_score = max(r.score for r in result.rounds)
    assert abs(result.best_score - max_round_score) < 1e-9


def test_autoresearch_deterministic_with_seed():
    r1 = run_autoresearch(EASY_PUZZLE, rounds=5, seed=123)
    r2 = run_autoresearch(EASY_PUZZLE, rounds=5, seed=123)
    for a, b in zip(r1.rounds, r2.rounds):
        assert a.strategy == b.strategy
        assert a.steps == b.steps


def test_autoresearch_with_subset():
    result = run_autoresearch(EASY_PUZZLE, rounds=5, strategies=["backtracking", "constraint"], seed=42)
    for r in result.rounds:
        assert r.strategy in ["backtracking", "constraint"]


def test_mutate_returns_valid_strategy():
    strategies = ["backtracking", "heuristic", "constraint"]
    for _ in range(20):
        assert mutate(strategies) in strategies


def test_autoresearch_round_zero_is_baseline():
    result = run_autoresearch(EASY_PUZZLE, rounds=3, seed=42)
    assert result.rounds[0].round_num == 0


# --- Ledger integration tests ---

def test_autoresearch_has_ledger():
    result = run_autoresearch(EASY_PUZZLE, rounds=5, seed=42)
    assert result.ledger is not None
    assert result.ledger.transaction_count == 5


def test_autoresearch_ledger_contains_all_rounds():
    result = run_autoresearch(EASY_PUZZLE, rounds=3, seed=42, ticket_id="sudoku_test")
    output = result.ledger.to_ledger_string()
    assert "sudoku_test" in output
    assert "SCORE" in output
    assert "STEPS" in output


def test_autoresearch_ledger_save(tmp_path):
    result = run_autoresearch(EASY_PUZZLE, rounds=3, seed=42)
    path = str(tmp_path / "autoresearch.ledger")
    result.ledger.save(path)
    with open(path) as f:
        content = f.read()
    assert "Eval:" in content
    assert "Budget:Score" in content
