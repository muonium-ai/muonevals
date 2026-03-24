# Scoring Analysis: Asymmetric Improvement Landscape

## Observation

| Direction | Start | End | Delta |
|-----------|------:|----:|------:|
| Best (improvement) | 0.7030 | 0.7261 | +0.0231 (~3.3%) |
| Worst (degradation) | 0.7015 | 0.3308 | -0.3707 (~53%) |

Improvements are rare and tiny. Degradation is easy and dramatic.

## Root Cause: The Scoring Formula

```
score = 0.6 * correctness + 0.2 * efficiency + 0.2 * speed
```

Where:
- `correctness(solution)` = 1.0 if valid, 0.0 otherwise (binary)
- `efficiency(steps)` = 1 / (1 + steps)
- `speed(time_ms)` = 1 / (1 + time_ms)

### Problem 1: Flat ceiling (efficiency/speed are near-zero)

At realistic step counts, the efficiency and speed components contribute almost nothing:

| Steps | efficiency | * 0.2 weight | Contribution |
|------:|-----------:|-------------:|-------------:|
| 80 | 0.0123 | 0.0025 | negligible |
| 455 | 0.0022 | 0.0004 | negligible |
| 3010 | 0.0003 | 0.00007 | ~zero |

Same for speed — `1/(1+326ms)` = 0.003, weighted to 0.0006.

Every config that solves all 6 puzzles scores ~0.60 + noise. The entire
best-score range (0.7030 to 0.7261) is differentiated by rounding in the
fourth decimal place. **There is almost no gradient to climb.**

### Problem 2: Steep cliff (correctness is binary)

Correctness is all-or-nothing per puzzle. With 6 puzzles:

| Solved | Correctness contribution | Score floor |
|-------:|-------------------------:|------------:|
| 6/6 | 0.600 | ~0.60 |
| 5/6 | 0.500 | ~0.50 |
| 4/6 | 0.400 | ~0.40 |
| 3/6 | 0.300 | ~0.30 |

Failing one puzzle drops the score by ~0.10 instantly. This is why the
worst configs (3/6 solved, score 0.33) are so far below the best (6/6
solved, score 0.73). There is no middle ground — a config either solves
a puzzle or gets zero credit for it.

### The Asymmetry

```
    1.0 |
        |
    0.8 |
        |  ......flat ceiling (all configs solving 6/6 land here)
    0.7 |  ======== best: 0.7261
        |  ======== start: 0.7030
    0.6 |  --------  correctness floor (6/6 solved)
        |
    0.5 |            cliff: lose 1 puzzle
        |
    0.4 |            cliff: lose 2 puzzles
        |
    0.3 |  ======== worst: 0.3308 (3/6 solved)
        |
    0.0 |
```

The search space above the 0.60 line is nearly flat (all variation comes
from efficiency/speed noise). Below it, every lost puzzle is a cliff.

## Proposed Fixes

### Option 1: Log-scale efficiency/speed (smallest change, biggest impact)

Replace `1/(1+x)` with `1/(1+log(1+x))` so that realistic step
reductions produce visible score changes:

| Steps | Current | Log-scale |
|------:|--------:|----------:|
| 80 | 0.012 | 0.185 |
| 455 | 0.002 | 0.140 |
| 3010 | 0.0003 | 0.108 |

With log-scale, reducing steps from 3010 to 80 improves the efficiency
component by 0.077 — weighted at 0.2, that is +0.015 on the final
score. Small but **visible and climbable**, unlike the current ~0.0002
difference.

### Option 2: Partial correctness

Instead of binary 0/1, score how many cells are correctly placed:

```python
def correctness(solution, puzzle):
    if not solution:
        return 0.0
    correct_cells = count_matching(solution, known_answer)
    return correct_cells / 81
```

A config that fills 78/81 cells before hitting max_steps scores 0.96
instead of 0.0. This eliminates the cliff and creates a smooth gradient
for the search to follow.

### Option 3: Relative scoring (baseline-normalized)

Score configs relative to a baseline rather than on an absolute scale:

```python
efficiency = baseline_steps / max(steps, 1)  # >1 means better than baseline
speed = baseline_time / max(time_ms, 0.01)
```

This makes improvements always proportional and visible regardless of
absolute magnitude.

## Applied Fix: Option 2 — Partial Correctness

**Implemented 2026-03-24.** Binary correctness replaced with partial credit.

### What changed

- `correctness(solution)` now returns `conflict_free_cells / 81` instead of
  binary 0/1. A grid with 70/81 conflict-free filled cells scores 0.864.
- `configurable_solver.solve_with_config()` returns the partial grid even on
  failure (previously returned `None`), enabling partial scoring.
- `score_result()` delegates to the updated `correctness()` scorer.

### Expected impact

The scoring landscape now has a smooth gradient instead of binary cliffs:

| Scenario | Old score | New score |
|----------|----------:|----------:|
| 6/6 solved | ~0.60 | ~0.60 |
| 5/6 solved, 1 partial (70/81) | ~0.50 | ~0.57 |
| 3/6 solved, 3 partial | ~0.30 | ~0.45 |
| All partial (avg 60/81) | ~0.00 | ~0.44 |

Configs that make progress on hard puzzles without fully solving them now
get credit, giving the search a gradient to follow instead of a cliff.

### Remaining options

Options 1 (log-scale efficiency/speed) and 3 (baseline-normalized) can
still be layered on top if the efficiency/speed components need more
dynamic range.

## Data Sources

- `best.tsv` — all-time best configs and scores
- `worst.tsv` — all-time worst configs and scores
- `ledgers/` — full experiment logs per run
- Scoring formula: `sudoku/evaluate.py:score_result()`
- Scorers: `muonevals/scorers.py`
