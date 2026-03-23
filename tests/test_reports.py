"""Tests for balance and register reports."""

from datetime import date

from muonevals.ledger import EvalLedger
from muonevals.reports import balance_report, register_report


def _make_ledger():
    ledger = EvalLedger()
    ledger.log("s1", 1, 0.62, 500, 120.0, strategy="backtracking",
               run_date=date(2026, 3, 23))
    ledger.log("s1", 2, 0.78, 200, 60.0, strategy="heuristic",
               run_date=date(2026, 3, 23))
    ledger.log("s1", 3, 0.91, 80, 30.0, strategy="constraint",
               run_date=date(2026, 3, 23))
    return ledger


def test_balance_report_shows_accounts():
    ledger = _make_ledger()
    report = balance_report(ledger)
    assert "Evals" in report
    assert "Budget" in report
    assert "SCORE" in report


def test_balance_report_flat():
    ledger = _make_ledger()
    report = balance_report(ledger, flat=True)
    assert "Evals:Score:backtracking" in report
    assert "Evals:Score:constraint" in report


def test_balance_report_filtered():
    ledger = _make_ledger()
    report = balance_report(ledger, accounts=["Evals:Score"], flat=True)
    assert "SCORE" in report
    assert "Evals:Score:backtracking" in report


def test_register_report_shows_transactions():
    ledger = _make_ledger()
    report = register_report(ledger, accounts=["Evals:Score"])
    assert "26-Mar-23" in report
    assert "SCORE" in report


def test_register_report_all():
    ledger = _make_ledger()
    report = register_report(ledger)
    assert "backtracking" in report
    assert "constraint" in report
