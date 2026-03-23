"""Tests for ledger export."""

import os
import tempfile
from datetime import date

from muonevals.export import export_eval_run


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


def test_export_creates_ledger_with_all_strategies():
    ledger = export_eval_run(EASY_PUZZLE, "sudoku_001")
    assert ledger.transaction_count == 3  # backtracking, heuristic, constraint


def test_export_with_subset():
    ledger = export_eval_run(EASY_PUZZLE, "s1",
                             strategies=["backtracking", "constraint"])
    assert ledger.transaction_count == 2


def test_export_to_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "evals.ledger")
        ledger = export_eval_run(EASY_PUZZLE, "sudoku_001",
                                 output_path=path,
                                 run_date=date(2026, 3, 23))
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "2026/03/23" in content
        assert "SCORE" in content
        assert "STEPS" in content
        assert "MS" in content


def test_export_ledger_string_contains_strategies():
    ledger = export_eval_run(EASY_PUZZLE, "s1", run_date=date(2026, 3, 23))
    output = ledger.to_ledger_string()
    assert "backtracking" in output
    assert "heuristic" in output
    assert "constraint" in output
