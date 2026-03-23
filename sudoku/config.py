"""Parameterized solver configuration — the mutable part of autoresearch.

Like train.py in Karpathy's autoresearch, this defines the knobs
that the experiment loop can mutate to search for improvements.
"""

from __future__ import annotations

import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SolverConfig:
    """Tunable solver parameters.

    Knobs:
        strategy: Which solver backend to use.
        use_propagation: Whether to propagate constraints after each placement.
        propagation_depth: How many rounds of naked-single propagation to run
                          (0 = unlimited, let it converge).
        candidate_ordering: How to order candidate values for each cell.
            - "ascending": 1..9 (default)
            - "descending": 9..1
            - "random": shuffled
            - "frequency": least-used values in peers first
        mrv: Use Minimum Remaining Values (pick cell with fewest candidates).
        max_steps: Abort after this many steps (0 = no limit).
    """

    strategy: str = "constraint"
    use_propagation: bool = True
    propagation_depth: int = 0  # 0 = unlimited
    candidate_ordering: str = "ascending"  # ascending, descending, random, frequency
    mrv: bool = True
    max_steps: int = 50000  # safety limit to prevent hanging

    def describe(self) -> str:
        """One-line description for logging."""
        parts = [self.strategy]
        if self.use_propagation:
            depth = "full" if self.propagation_depth == 0 else str(self.propagation_depth)
            parts.append(f"prop={depth}")
        else:
            parts.append("no-prop")
        parts.append(f"order={self.candidate_ordering}")
        parts.append(f"mrv={'on' if self.mrv else 'off'}")
        parts.append(f"max={self.max_steps}")
        return " | ".join(parts)


# The space of valid values for each knob
STRATEGIES = ["backtracking", "heuristic", "constraint"]
ORDERINGS = ["ascending", "descending", "random", "frequency"]
PROPAGATION_DEPTHS = [0, 1, 2, 3, 5]
MAX_STEPS_OPTIONS = [10000, 50000, 100000]


def mutate_config(config: SolverConfig, seed: Optional[int] = None) -> SolverConfig:
    """Mutate a config by changing one random knob.

    Like Karpathy's agent proposing one change per experiment,
    we change exactly one parameter to isolate the effect.
    """
    if seed is not None:
        random.seed(seed)

    new = deepcopy(config)
    knob = random.choice(["strategy", "propagation", "ordering", "mrv", "prop_depth"])

    if knob == "strategy":
        choices = [s for s in STRATEGIES if s != config.strategy]
        new.strategy = random.choice(choices)
    elif knob == "propagation":
        new.use_propagation = not config.use_propagation
    elif knob == "ordering":
        choices = [o for o in ORDERINGS if o != config.candidate_ordering]
        new.candidate_ordering = random.choice(choices)
    elif knob == "mrv":
        new.mrv = not config.mrv
    elif knob == "prop_depth":
        choices = [d for d in PROPAGATION_DEPTHS if d != config.propagation_depth]
        new.propagation_depth = random.choice(choices)

    return new
