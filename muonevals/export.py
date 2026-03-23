"""Export eval results to ledger format.

Ties together the eval pipeline: run strategies, log to EvalLedger,
and export to a .ledger file that muonledger can read.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from muonevals.ledger import EvalLedger
from sudoku.evaluate import evaluate_all, StrategyResult
from sudoku.solver import Grid


def export_eval_run(
    grid: Grid,
    ticket_id: str,
    strategies: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    run_date: Optional[date] = None,
) -> EvalLedger:
    """Run all strategies on a grid and export results to a ledger.

    Args:
        grid: 9x9 Sudoku puzzle.
        ticket_id: Ticket identifier for ledger entries.
        strategies: Strategy names to evaluate. Defaults to all.
        output_path: If provided, saves the ledger to this file.
        run_date: Date for ledger entries. Defaults to today.

    Returns:
        The EvalLedger with all entries.
    """
    ledger = EvalLedger()
    results = evaluate_all(grid, strategies)

    for i, result in enumerate(results, start=1):
        ledger.log(
            ticket_id=ticket_id,
            attempt_id=i,
            score=result.score,
            steps=result.steps,
            time_ms=result.time_ms,
            strategy=result.strategy,
            run_date=run_date,
        )

    if output_path:
        ledger.save(output_path)

    return ledger
