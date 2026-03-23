"""Tests for results table and summary."""

import os
import tempfile

from sudoku.experiment import run_experiments
from sudoku.results import results_to_tsv, save_results_tsv, summary_table


def _make_run():
    return run_experiments(num_experiments=3, seed=42)


def test_results_to_tsv():
    run = _make_run()
    tsv = results_to_tsv(run)
    lines = tsv.strip().split("\n")
    assert lines[0].startswith("id\t")
    assert len(lines) == 4  # header + 3 experiments


def test_save_results_tsv_default():
    run = _make_run()
    path = save_results_tsv(run)
    assert path.endswith("_results.tsv")
    assert os.path.exists(path)


def test_save_results_tsv_custom_path():
    run = _make_run()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "results.tsv")
        returned = save_results_tsv(run, path)
        assert returned == path
        with open(path) as f:
            content = f.read()
        assert "baseline" in content


def test_summary_table():
    run = _make_run()
    table = summary_table(run)
    assert "AUTORESEARCH EXPERIMENT SUMMARY" in table
    assert "Baseline score:" in table
    assert "Best score:" in table
    assert "Improvement:" in table
    assert "Best config:" in table
