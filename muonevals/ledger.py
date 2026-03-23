"""Ledger logging for MuonLedger integration."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional


def log_ledger(ticket_id: str, attempt_id: int, score: float,
               steps: int, time_ms: float,
               strategy: Optional[str] = None,
               ledger_file: Optional[str] = None) -> dict:
    """Record an eval run to the ledger.

    If ledger_file is provided, appends the entry as JSON-lines.
    Always returns the entry dict.
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
