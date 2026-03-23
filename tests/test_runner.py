"""Tests for the eval runner."""

import pytest
from muonevals.eval import Eval
from muonevals.runner import run_eval


def test_run_eval_perfect_score():
    agent = lambda x: x
    dataset = [1, 1, 1]
    e = Eval(scorer=lambda output: 1.0 if output == 1 else 0.0)
    assert run_eval(agent, dataset, e) == 1.0


def test_run_eval_zero_score():
    agent = lambda x: x
    dataset = [0, 0, 0]
    e = Eval(scorer=lambda output: 1.0 if output == 1 else 0.0)
    assert run_eval(agent, dataset, e) == 0.0


def test_run_eval_mixed_scores():
    agent = lambda x: x
    dataset = [1, 0, 1, 0]
    e = Eval(scorer=lambda output: 1.0 if output == 1 else 0.0)
    assert run_eval(agent, dataset, e) == 0.5


def test_run_eval_single_item():
    agent = lambda x: x * 2
    dataset = [5]
    e = Eval(scorer=lambda output: 0.8)
    assert run_eval(agent, dataset, e) == 0.8


def test_run_eval_empty_dataset():
    agent = lambda x: x
    e = Eval(scorer=lambda output: 1.0)
    with pytest.raises(ValueError):
        run_eval(agent, [], e)


def test_run_eval_agent_transforms_input():
    agent = lambda x: x.upper()
    dataset = ["hello", "world"]
    e = Eval(scorer=lambda output: 1.0 if output.isupper() else 0.0)
    assert run_eval(agent, dataset, e) == 1.0
