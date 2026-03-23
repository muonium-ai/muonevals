"""Tests for the Eval base class."""

import pytest
from muonevals.eval import Eval


def test_eval_returns_score():
    e = Eval(scorer=lambda x: 0.5)
    assert e.run("anything") == 0.5


def test_eval_passes_output_to_scorer():
    e = Eval(scorer=lambda x: 1.0 if x == "correct" else 0.0)
    assert e.run("correct") == 1.0
    assert e.run("wrong") == 0.0


def test_eval_score_boundaries():
    assert Eval(scorer=lambda x: 0.0).run(None) == 0.0
    assert Eval(scorer=lambda x: 1.0).run(None) == 1.0


def test_eval_rejects_score_above_one():
    e = Eval(scorer=lambda x: 1.5)
    with pytest.raises(ValueError):
        e.run(None)


def test_eval_rejects_negative_score():
    e = Eval(scorer=lambda x: -0.1)
    with pytest.raises(ValueError):
        e.run(None)
