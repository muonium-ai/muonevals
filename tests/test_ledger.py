"""Tests for ledger logging."""

import json
import os
import tempfile

from muonevals.ledger import log_ledger


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
