"""Tests for built-in scorers."""

from muonevals.scorers import correctness, efficiency, speed


def test_correctness_valid():
    assert correctness(True) == 1.0
    assert correctness([1, 2, 3]) == 1.0


def test_correctness_invalid():
    assert correctness(False) == 0.0
    assert correctness(None) == 0.0
    assert correctness([]) == 0.0


def test_efficiency_zero_steps():
    assert efficiency(0) == 1.0


def test_efficiency_decreases_with_steps():
    assert efficiency(1) == 0.5
    assert efficiency(9) == 0.1
    assert efficiency(99) == 0.01


def test_efficiency_always_positive():
    assert efficiency(1000000) > 0


def test_speed_zero_time():
    assert speed(0) == 1.0


def test_speed_decreases_with_time():
    assert speed(1) == 0.5
    assert speed(9) == 0.1


def test_speed_always_positive():
    assert speed(1000000) > 0


def test_all_scorers_return_normalized():
    for val in [correctness(True), correctness(False),
                efficiency(0), efficiency(100),
                speed(0), speed(100)]:
        assert 0 <= val <= 1
