"""Ledger logging for MuonLedger integration.

Uses muonledger's Journal/Transaction/Post API to record eval runs
as proper double-entry ledger transactions.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from typing import Optional

from muonledger.journal import Journal
from muonledger.xact import Transaction
from muonledger.post import Post
from muonledger.amount import Amount
from muonledger.commands.print_cmd import print_command


class EvalLedger:
    """A ledger that records eval runs as double-entry transactions.

    Each eval run creates a transaction with postings for score, steps,
    and time against corresponding budget accounts.

    Account structure:
        Evals:Score:<strategy>    — score achieved
        Evals:Steps:<strategy>    — steps taken
        Evals:Time:<strategy>     — time spent (ms)
        Budget:Score              — balancing account for scores
        Budget:Steps              — balancing account for steps
        Budget:Time               — balancing account for time
    """

    def __init__(self) -> None:
        self.journal = Journal()

    def log(self, ticket_id: str, attempt_id: int, score: float,
            steps: int, time_ms: float,
            strategy: Optional[str] = None,
            run_date: Optional[date] = None) -> Transaction:
        """Record an eval run as a ledger transaction.

        Returns the Transaction that was added to the journal.
        """
        label = strategy or "unknown"
        run_date = run_date or date.today()

        xact = Transaction(payee=f"Eval: {ticket_id} attempt #{attempt_id}")
        xact.date = run_date
        if strategy:
            xact.set_tag("strategy", strategy)
        xact.set_tag("ticket", ticket_id)
        xact.set_tag("attempt", str(attempt_id))

        # Score posting
        score_acct = self.journal.find_account(f"Evals:Score:{label}")
        budget_score = self.journal.find_account("Budget:Score")
        xact.add_post(Post(account=score_acct, amount=Amount(f"{score:.4f} SCORE")))
        xact.add_post(Post(account=budget_score, amount=Amount(f"{-score:.4f} SCORE")))

        # Steps posting
        steps_acct = self.journal.find_account(f"Evals:Steps:{label}")
        budget_steps = self.journal.find_account("Budget:Steps")
        xact.add_post(Post(account=steps_acct, amount=Amount(f"{steps} STEPS")))
        xact.add_post(Post(account=budget_steps, amount=Amount(f"{-steps} STEPS")))

        # Time posting
        time_acct = self.journal.find_account(f"Evals:Time:{label}")
        budget_time = self.journal.find_account("Budget:Time")
        xact.add_post(Post(account=time_acct, amount=Amount(f"{time_ms:.2f} MS")))
        xact.add_post(Post(account=budget_time, amount=Amount(f"{-time_ms:.2f} MS")))

        self.journal.add_xact(xact)
        return xact

    def to_ledger_string(self) -> str:
        """Serialize the journal to ledger-format text."""
        return print_command(self.journal)

    def save(self, path: Optional[str] = None) -> str:
        """Write the journal to a .ledger file.

        Args:
            path: File path. If None, saves to ledgers/<timestamp>.ledger
                  relative to the project root.

        Returns:
            The path the file was written to.
        """
        if path is None:
            ledgers_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "ledgers"
            )
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            path = os.path.join(ledgers_dir, f"{ts}.ledger")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_ledger_string())
        return path

    @property
    def transaction_count(self) -> int:
        return len(self.journal.xacts)


# Backward-compatible convenience function
def log_ledger(ticket_id: str, attempt_id: int, score: float,
               steps: int, time_ms: float,
               strategy: Optional[str] = None,
               ledger_file: Optional[str] = None) -> dict:
    """Record an eval run to a JSON-lines file (legacy convenience).

    For full muonledger integration, use EvalLedger instead.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket": ticket_id,
        "attempt": attempt_id,
        "score": score,
        "steps": steps,
        "time_ms": time_ms,
    }
    if strategy is not None:
        entry["strategy"] = strategy

    if ledger_file is not None:
        os.makedirs(os.path.dirname(ledger_file) or ".", exist_ok=True)
        with open(ledger_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    return entry
