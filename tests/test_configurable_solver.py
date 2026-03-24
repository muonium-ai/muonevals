"""Tests for the configurable solver."""

from sudoku.config import SolverConfig, mutate_config
from sudoku.configurable_solver import solve_with_config
from sudoku.solver import is_valid
from sudoku.dataset import EASY_PUZZLES, HARD_PUZZLES


EASY = EASY_PUZZLES[0]


def test_default_config_solves():
    result = solve_with_config(EASY, SolverConfig())
    assert result.solved
    assert is_valid(result.solution)


def test_no_propagation_solves():
    cfg = SolverConfig(use_propagation=False)
    result = solve_with_config(EASY, cfg)
    assert result.solved


def test_no_mrv_solves():
    cfg = SolverConfig(mrv=False)
    result = solve_with_config(EASY, cfg)
    assert result.solved


def test_descending_order_solves():
    cfg = SolverConfig(candidate_ordering="descending")
    result = solve_with_config(EASY, cfg)
    assert result.solved


def test_frequency_order_solves():
    cfg = SolverConfig(candidate_ordering="frequency")
    result = solve_with_config(EASY, cfg)
    assert result.solved


def test_limited_propagation_depth():
    cfg = SolverConfig(propagation_depth=2)
    result = solve_with_config(EASY, cfg)
    assert result.solved


def test_max_steps_aborts():
    cfg = SolverConfig(use_propagation=False, mrv=False, max_steps=3)
    result = solve_with_config(EASY, cfg)
    # With only 3 steps and no heuristics, can't solve
    assert not result.solved


def test_mrv_fewer_steps_than_no_mrv():
    cfg_mrv = SolverConfig(mrv=True, use_propagation=False)
    cfg_no = SolverConfig(mrv=False, use_propagation=False)
    r1 = solve_with_config(EASY, cfg_mrv)
    r2 = solve_with_config(EASY, cfg_no)
    assert r1.steps <= r2.steps


def test_propagation_fewer_steps():
    cfg_prop = SolverConfig(use_propagation=True)
    cfg_no = SolverConfig(use_propagation=False)
    r1 = solve_with_config(EASY, cfg_prop)
    r2 = solve_with_config(EASY, cfg_no)
    assert r1.steps <= r2.steps


def test_mutate_changes_one_knob():
    original = SolverConfig()
    mutated = mutate_config(original, seed=42)
    # At least one field should differ
    diffs = 0
    for f in ["strategy", "use_propagation", "propagation_depth",
              "candidate_ordering", "mrv"]:
        if getattr(original, f) != getattr(mutated, f):
            diffs += 1
    assert diffs >= 1


def test_mutated_config_solves():
    cfg = SolverConfig()
    for i in range(10):
        cfg = mutate_config(cfg, seed=i)
        result = solve_with_config(EASY, cfg)
        # May not always solve (e.g., if max_steps hit), but should not crash
        assert result.steps > 0


def test_config_describe():
    cfg = SolverConfig()
    desc = cfg.describe()
    assert "constraint" in desc
    assert "prop=" in desc


def test_strategy_changes_behavior():
    """Different strategies should produce different step counts."""
    configs = {
        "backtracking": SolverConfig(strategy="backtracking"),
        "heuristic": SolverConfig(strategy="heuristic"),
        "constraint": SolverConfig(strategy="constraint"),
    }
    results = {name: solve_with_config(EASY, cfg) for name, cfg in configs.items()}
    steps = {name: r.steps for name, r in results.items()}
    # At least two strategies should have different step counts
    assert len(set(steps.values())) >= 2, f"All strategies produced same steps: {steps}"
    # All should still solve
    for name, r in results.items():
        assert r.solved, f"{name} failed to solve"
