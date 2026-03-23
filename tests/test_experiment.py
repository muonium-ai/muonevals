"""Tests for the autoresearch experiment loop."""

from sudoku.experiment import evaluate_config, run_experiments
from sudoku.config import SolverConfig


def test_evaluate_config_returns_experiment():
    exp = evaluate_config(SolverConfig())
    assert exp.mean_score > 0
    assert exp.total_count == 6
    assert exp.solved_count > 0


def test_run_experiments_baseline():
    run = run_experiments(num_experiments=1, seed=42)
    assert len(run.experiments) == 1
    assert run.experiments[0].status == "baseline"
    assert run.best_score > 0


def test_run_experiments_loop():
    run = run_experiments(num_experiments=5, seed=42)
    assert len(run.experiments) == 5
    assert run.total_experiments == 5
    assert run.best_config is not None


def test_run_experiments_logs_to_ledger():
    run = run_experiments(num_experiments=3, seed=42)
    assert run.ledger is not None
    assert run.ledger.transaction_count == 3


def test_run_experiments_best_score_monotonic():
    """Best score should never decrease."""
    run = run_experiments(num_experiments=10, seed=42)
    best = 0
    for exp in run.experiments:
        if exp.status in ("baseline", "improved"):
            assert exp.mean_score >= best
            best = exp.mean_score


def test_run_experiments_has_improvements_or_regressions():
    run = run_experiments(num_experiments=10, seed=42)
    statuses = {e.status for e in run.experiments}
    assert "baseline" in statuses
    # Should have at least some regressed or improved
    assert len(statuses) > 1
