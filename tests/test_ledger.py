"""Tests for ledger logging."""

import json
import os
import tempfile
from datetime import date

from muonevals.ledger import EvalLedger, log_ledger


# --- EvalLedger (muonledger integration) tests ---

def test_eval_ledger_log_creates_transaction():
    ledger = EvalLedger()
    xact = ledger.log("sudoku_001", 1, 0.85, 200, 60.0, strategy="backtracking")
    assert ledger.transaction_count == 1
    assert xact.payee == "Eval: sudoku_001 attempt #1"


def test_eval_ledger_multiple_entries():
    ledger = EvalLedger()
    ledger.log("s1", 1, 0.62, 500, 120.0, strategy="backtracking")
    ledger.log("s1", 2, 0.78, 200, 60.0, strategy="heuristic")
    ledger.log("s1", 3, 0.91, 80, 30.0, strategy="constraint")
    assert ledger.transaction_count == 3


def test_eval_ledger_to_ledger_string():
    ledger = EvalLedger()
    ledger.log("s1", 1, 0.62, 500, 120.0, strategy="backtracking",
               run_date=date(2026, 3, 23))
    output = ledger.to_ledger_string()
    assert "Eval: s1 attempt #1" in output
    assert "Evals:Score:backtracking" in output
    assert "SCORE" in output
    assert "STEPS" in output
    assert "MS" in output
    assert "2026/03/23" in output


def test_eval_ledger_save_to_file():
    ledger = EvalLedger()
    ledger.log("s1", 1, 0.62, 500, 120.0, strategy="backtracking",
               run_date=date(2026, 3, 23))
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "evals.ledger")
        returned_path = ledger.save(path)
        assert returned_path == path
        with open(path) as f:
            content = f.read()
        assert "Evals:Score:backtracking" in content
        assert "Budget:Score" in content


def test_eval_ledger_save_default_path():
    ledger = EvalLedger()
    ledger.log("s1", 1, 0.62, 500, 120.0, strategy="backtracking")
    path = ledger.save()
    assert path.endswith(".ledger")
    assert "ledgers" in path
    assert os.path.exists(path)
    # Clean up
    os.remove(path)


def test_eval_ledger_without_strategy():
    ledger = EvalLedger()
    ledger.log("s1", 1, 0.5, 100, 50.0)
    output = ledger.to_ledger_string()
    assert "Evals:Score:unknown" in output


def test_eval_ledger_transactions_balance():
    """Each transaction should have balanced postings (debits = credits)."""
    ledger = EvalLedger()
    ledger.log("s1", 1, 0.91, 80, 30.0, strategy="constraint")
    # If transactions didn't balance, add_xact would raise BalanceError
    assert ledger.transaction_count == 1


def test_eval_ledger_tags():
    ledger = EvalLedger()
    xact = ledger.log("sudoku_001", 2, 0.85, 200, 60.0, strategy="heuristic")
    assert xact.get_tag("ticket") == "sudoku_001"
    assert xact.get_tag("attempt") == "2"
    assert xact.get_tag("strategy") == "heuristic"


# --- Legacy log_ledger tests ---

def test_log_ledger_returns_entry():
    entry = log_ledger("sudoku_001", 1, 0.85, 200, 60.0)
    assert entry["ticket"] == "sudoku_001"
    assert entry["attempt"] == 1
    assert entry["score"] == 0.85
    assert entry["steps"] == 200
    assert entry["time_ms"] == 60.0
    assert "timestamp" in entry


def test_log_ledger_with_strategy():
    entry = log_ledger("s1", 1, 0.9, 80, 30.0, strategy="constraint")
    assert entry["strategy"] == "constraint"


def test_log_ledger_without_strategy():
    entry = log_ledger("s1", 1, 0.5, 100, 50.0)
    assert "strategy" not in entry


def test_log_ledger_writes_to_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "eval.jsonl")
        log_ledger("s1", 1, 0.6, 500, 120.0, ledger_file=path)
        log_ledger("s1", 2, 0.9, 80, 30.0, strategy="constraint", ledger_file=path)

        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 2
        first = json.loads(lines[0])
        assert first["ticket"] == "s1"
        assert first["attempt"] == 1
        second = json.loads(lines[1])
        assert second["attempt"] == 2
        assert second["strategy"] == "constraint"


def test_log_ledger_creates_parent_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "sub", "dir", "eval.jsonl")
        log_ledger("s1", 1, 0.5, 100, 50.0, ledger_file=path)
        assert os.path.exists(path)
