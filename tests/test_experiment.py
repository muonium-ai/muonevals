"""Tests for the autoresearch experiment loop."""

from sudoku import best
from sudoku.experiment import evaluate_config, run_experiments, Experiment
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


def test_schedule_zero_explore_zero_random():
    """Requesting 0% explore and 0% random should produce zero of each."""
    from sudoku.experiment import _build_strategy_schedule
    schedule = _build_strategy_schedule(10, 1.0, 0.0, 0.0)
    assert "explore" not in schedule
    assert "random" not in schedule
    assert all(s == "exploit" for s in schedule)


def test_schedule_invalid_total_raises():
    """Percentages totaling more than 1.0 should raise ValueError."""
    from sudoku.experiment import _build_strategy_schedule
    import pytest
    with pytest.raises(ValueError):
        _build_strategy_schedule(10, 0.2, 0.8, 0.8)


def test_schedule_negative_pct_raises():
    """Negative percentages should raise ValueError."""
    from sudoku.experiment import _build_strategy_schedule
    import pytest
    with pytest.raises(ValueError):
        _build_strategy_schedule(10, -0.1, 0.6, 0.5)


def test_schedule_length_matches_slots():
    """Schedule length should equal num_experiments - 1."""
    from sudoku.experiment import _build_strategy_schedule
    schedule = _build_strategy_schedule(11, 0.6, 0.2, 0.2)
    assert len(schedule) == 10


def test_schedule_pct_over_one_raises():
    from sudoku.experiment import _build_strategy_schedule
    import pytest
    with pytest.raises(ValueError):
        _build_strategy_schedule(10, 1.5, 0.0, 0.0)


def test_check_and_commit_returns_false_on_git_failure(monkeypatch, tmp_path):
    """check_and_commit should return False if commit_best returns None."""
    # Create a fake best.tsv with header only (score 0)
    fake_best = tmp_path / "best.tsv"
    fake_best.write_text("timestamp\tscore\tsteps\ttime_ms\tsolved\tconfig\n")
    monkeypatch.setattr(best, "BEST_FILE", str(fake_best))

    # Make commit_best always return None (simulating git failure)
    monkeypatch.setattr(best, "commit_best", lambda exp: None)

    exp = Experiment(
        experiment_id=1,
        config=SolverConfig(),
        description="test",
        mean_score=0.99,
        mean_steps=100,
        mean_time_ms=50,
        solved_count=6,
        total_count=6,
        status="improved",
        wall_time_ms=100,
    )
    result = best.check_and_commit(exp)
    assert result is False


def test_check_and_commit_returns_true_on_git_success(monkeypatch, tmp_path):
    """check_and_commit should return True if commit_best returns a commit hash."""
    fake_best = tmp_path / "best.tsv"
    fake_best.write_text("timestamp\tscore\tsteps\ttime_ms\tsolved\tconfig\n")
    monkeypatch.setattr(best, "BEST_FILE", str(fake_best))

    monkeypatch.setattr(best, "commit_best", lambda exp: "abc1234")

    exp = Experiment(
        experiment_id=1,
        config=SolverConfig(),
        description="test",
        mean_score=0.99,
        mean_steps=100,
        mean_time_ms=50,
        solved_count=6,
        total_count=6,
        status="improved",
        wall_time_ms=100,
    )
    result = best.check_and_commit(exp)
    assert result is True
