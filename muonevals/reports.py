"""Balance and register reports for eval runs using muonledger."""

from __future__ import annotations

from typing import List, Optional

from muonledger.commands.balance import balance_command
from muonledger.commands.register import register_command

from muonevals.ledger import EvalLedger


def balance_report(ledger: EvalLedger, accounts: Optional[List[str]] = None,
                   flat: bool = False) -> str:
    """Generate a balance report from the eval ledger.

    Args:
        ledger: EvalLedger with logged eval runs.
        accounts: Optional account patterns to filter (e.g. ["Evals:Score"]).
        flat: If True, show flat account list instead of tree.

    Returns:
        Formatted balance report string.
    """
    args = []
    if flat:
        args.append("--flat")
    if accounts:
        args.extend(accounts)
    return balance_command(ledger.journal, args)


def register_report(ledger: EvalLedger, accounts: Optional[List[str]] = None,
                    wide: bool = True) -> str:
    """Generate a register report from the eval ledger.

    Args:
        ledger: EvalLedger with logged eval runs.
        accounts: Optional account patterns to filter.
        wide: If True, use wide format.

    Returns:
        Formatted register report string.
    """
    args = []
    if wide:
        args.append("--wide")
    if accounts:
        args.extend(accounts)
    return register_command(ledger.journal, args)
