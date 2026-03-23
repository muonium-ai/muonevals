"""Tests for EvalTicket structure."""

import pytest
from muonevals.ticket import EvalTicket


def test_create_ticket():
    t = EvalTicket(id="sudoku_001", title="Solve Sudoku efficiently", target_score=0.95)
    assert t.id == "sudoku_001"
    assert t.target_score == 0.95
    assert t.attempts == []


def test_invalid_target_score():
    with pytest.raises(ValueError):
        EvalTicket(id="x", title="x", target_score=0.0)
    with pytest.raises(ValueError):
        EvalTicket(id="x", title="x", target_score=1.5)


def test_add_attempt():
    t = EvalTicket(id="s1", title="test", target_score=0.9)
    a = t.add_attempt(score=0.62, steps=500, time_ms=120, strategy="backtracking")
    assert a.attempt_id == 1
    assert a.score == 0.62
    assert len(t.attempts) == 1


def test_multiple_attempts_and_best():
    t = EvalTicket(id="s1", title="test", target_score=0.9)
    t.add_attempt(score=0.62, steps=500, time_ms=120, strategy="basic")
    t.add_attempt(score=0.91, steps=80, time_ms=30, strategy="constraint")
    t.add_attempt(score=0.78, steps=200, time_ms=60, strategy="heuristic")
    assert t.best_attempt.score == 0.91
    assert t.best_attempt.strategy == "constraint"


def test_met_target():
    t = EvalTicket(id="s1", title="test", target_score=0.9)
    assert not t.met_target
    t.add_attempt(score=0.5, steps=100, time_ms=50)
    assert not t.met_target
    t.add_attempt(score=0.95, steps=50, time_ms=20)
    assert t.met_target


def test_to_dict():
    t = EvalTicket(id="s1", title="test", target_score=0.9)
    t.add_attempt(score=0.8, steps=100, time_ms=50, strategy="basic")
    d = t.to_dict()
    assert d["ticket"]["id"] == "s1"
    assert d["ticket"]["target_score"] == 0.9
    assert len(d["attempts"]) == 1
    assert d["attempts"][0]["strategy"] == "basic"
