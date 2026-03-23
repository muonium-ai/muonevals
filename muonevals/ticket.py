"""Eval ticket structure for MuonTickets integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Attempt:
    """A single evaluation attempt against a ticket."""

    attempt_id: int
    score: float
    steps: int
    time_ms: float
    strategy: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.score >= 1.0  # caller checks against target


@dataclass
class EvalTicket:
    """Ticket that tracks an evaluation goal with multiple attempts.

    Maps to the MuonTickets YAML structure:
        ticket:
          id: sudoku_001
          title: "Solve Sudoku efficiently"
          target_score: 0.95
    """

    id: str
    title: str
    target_score: float
    attempts: List[Attempt] = field(default_factory=list)

    def __post_init__(self):
        if not (0 < self.target_score <= 1):
            raise ValueError(f"target_score must be in (0, 1], got {self.target_score}")

    def add_attempt(self, score: float, steps: int, time_ms: float,
                    strategy: Optional[str] = None) -> Attempt:
        attempt = Attempt(
            attempt_id=len(self.attempts) + 1,
            score=score,
            steps=steps,
            time_ms=time_ms,
            strategy=strategy,
        )
        self.attempts.append(attempt)
        return attempt

    @property
    def best_attempt(self) -> Optional[Attempt]:
        if not self.attempts:
            return None
        return max(self.attempts, key=lambda a: a.score)

    @property
    def met_target(self) -> bool:
        best = self.best_attempt
        return best is not None and best.score >= self.target_score

    def to_dict(self) -> dict:
        return {
            "ticket": {
                "id": self.id,
                "title": self.title,
                "target_score": self.target_score,
            },
            "attempts": [
                {
                    "attempt_id": a.attempt_id,
                    "score": a.score,
                    "steps": a.steps,
                    "time_ms": a.time_ms,
                    "strategy": a.strategy,
                }
                for a in self.attempts
            ],
        }
