# Muon Autoresearch Sudoku System  
## Requirements & Implementation Guide

---

# 🧠 Overview

This document describes how to:

1. Build **muonevals in Python**
2. Integrate with **MuonTickets + MuonLedger**
3. Build a **Sudoku solver**
4. Add an **autoresearch loop**

Everything is broken into **phases** and **tickets**.

---

# 📦 Phase 1: Build muonevals (Python)

## 🎫 Ticket MT-001: Eval Base Class

**Task:**
Implement a base Eval class.

```python
class Eval:
    def __init__(self, scorer):
        self.scorer = scorer

    def run(self, output):
        return self.scorer(output)
```

**Acceptance Criteria:**
- Returns score between 0 and 1

---

## 🎫 Ticket MT-002: Implement Scorers

**Task:**
Create scorers:

```python
def correctness(solution):
    return 1 if is_valid(solution) else 0

def efficiency(steps):
    return 1 / (1 + steps)

def speed(time_ms):
    return 1 / (1 + time_ms)
```

**Acceptance Criteria:**
- Each scorer returns normalized value

---

## 🎫 Ticket MT-003: Eval Runner

**Task:**
Run eval on dataset

```python
def run_eval(agent, dataset, eval):
    scores = []
    for item in dataset:
        output = agent.run(item)
        score = eval.run(output)
        scores.append(score)
    return sum(scores) / len(scores)
```

**Acceptance Criteria:**
- Aggregated score returned

---

# 🔗 Phase 2: MuonTickets + MuonLedger Integration

## 🎫 Ticket MT-004: Ticket Structure

```yaml
ticket:
  id: sudoku_001
  title: "Solve Sudoku efficiently"
  target_score: 0.75
```

**Target Score Rationale:**
The combined score formula is `0.6 * correctness + 0.2 * efficiency + 0.2 * speed`.
With correctness capped at 0.6, a perfect solve (0 steps, 0ms) yields 1.0, but
realistic solvers score 0.70–0.73 (current best: 0.7261). A target of 0.75
represents a meaningful improvement over baseline while remaining achievable.
Scores above 0.80 would require near-zero steps and sub-millisecond times.

**Acceptance Criteria:**
- Supports multiple attempts

---

## 🎫 Ticket MT-005: Ledger Logging

```python
def log_ledger(ticket_id, attempt_id, score, steps, time):
    print({
        "ticket": ticket_id,
        "attempt": attempt_id,
        "score": score,
        "steps": steps,
        "time": time
    })
```

**Acceptance Criteria:**
- Every run recorded as a TSV row in `ledger/` with fields:
  `date`, `ticket_id`, `attempt_id`, `score`, `steps`, `time_ms`, `strategy`
- Ledger files stored under `ledger/` directory, one file per session
- Ledger is append-only within a session; no in-place edits

---

# 🧩 Phase 3: Sudoku Solver

## 🎫 Ticket MT-006: Backtracking Solver

**Task:**
Implement basic solver

```python
def solve(grid):
    # backtracking logic
    pass
```

**Acceptance Criteria:**
- Solves valid puzzles

---

## 🎫 Ticket MT-007: Heuristic

**Task:**
Add least-candidate strategy

**Acceptance Criteria:**
- Fewer steps than baseline

---

## 🎫 Ticket MT-008: Constraint Propagation

**Task:**
Improve solver using constraints

**Acceptance Criteria:**
- Faster solve

---

# 🔁 Phase 4: Autoresearch Loop

Phase 4 uses a **two-level search**:

1. **Solver backend** (strategy registry): selects which algorithm runs —
   `backtracking`, `heuristic`, or `constraint`. Each backend enforces
   specific structural constraints (e.g., backtracking disables propagation
   and MRV).
2. **Config knobs** (SolverConfig): tunable parameters within a backend —
   `candidate_ordering`, `use_propagation`, `propagation_depth`, `mrv`,
   `max_steps`. The experiment loop mutates one knob per iteration.

The three **search strategies** (`exploit`, `explore`, `random`) control
*how* new configs are generated, not which solver backend runs.

## 🎫 Ticket MT-009: Solver Backends (Strategy Registry)

```python
# Strategy registry — solver backend selection
solver_backends = {
    "backtracking": solve,           # pure backtracking, no heuristics
    "heuristic": solve_heuristic,    # MRV cell selection
    "constraint": solve_constraint,  # propagation + MRV
}
```

---

## 🎫 Ticket MT-010: Evaluate Configs

Score formula: `0.6 * correctness + 0.2 * efficiency + 0.2 * speed`

Where:
- `correctness(solution)` = 1.0 if valid 9x9 Sudoku grid, 0.0 otherwise
- `efficiency(steps)` = 1 / (1 + steps), steps must be non-negative
- `speed(time_ms)` = 1 / (1 + time_ms), time_ms must be non-negative

```python
results = []
for label, grid in dataset:
    result = solve_with_config(grid, config)
    score = score_result(result.solution, result.steps, result.time_ms)
    results.append(score)

mean_score = sum(results) / len(results)
```

**Acceptance Criteria:**
- Scoring formula is `0.6 * correctness + 0.2 * efficiency + 0.2 * speed`
- All scorers return values in [0, 1]; negative inputs raise `ValueError`
- Correctness rejects structurally invalid grids (wrong size, non-int values, duplicates)
- Mean score computed over the fixed dataset of 6 puzzles (2 easy, 2 medium, 2 hard)

**Dataset specification:**
- Fixed set: 2 easy (~30 empties), 2 medium (~45 empties), 2 hard (~55 empties)
- Total: 6 puzzles, defined in `sudoku/dataset.py`
- Dataset is immutable across experiments to ensure fair comparison

**Deterministic runs:**
- When a `seed` is provided, the experiment sequence is fully reproducible
- Same seed + same dataset = same config sequence and same scores

---

## 🎫 Ticket MT-011: Config Mutation Loop

Each iteration mutates **one config knob** to isolate its effect:

```python
for i in range(num_experiments):
    # search_strategy determines HOW to generate the candidate:
    #   exploit: mutate one knob from current best
    #   explore: start from a different backend, randomize 2-3 knobs
    #   random:  fully random config
    candidate = generate_config(best, search_strategy)
    score = evaluate(candidate)
    if score > best_score:
        best = candidate
```

Allowed mutations: `strategy`, `use_propagation`, `propagation_depth`,
`candidate_ordering`, `mrv`, `max_steps`.

**Acceptance Criteria:**
- `mutate` changes exactly one knob per call
- Allowed knobs: `strategy`, `use_propagation`, `propagation_depth`,
  `candidate_ordering`, `mrv`, `max_steps`
- Search-mix percentages (`exploit_pct`, `explore_pct`, `random_pct`) must
  each be in [0.0, 1.0] and sum to 1.0; violation raises `ValueError`
- Setting a strategy percentage to 0% produces zero runs of that type
- Best score is monotonically non-decreasing across the run

---

# 🚀 Output Example

| Strategy | Steps | Time | Score |
|----------|------:|-----:|------:|
| Basic | 500 | 120ms | 0.60 |
| Heuristic | 200 | 60ms | 0.70 |
| Constraint | 80 | 30ms | 0.73 |

---

# 🧠 Final Insight

```
muontickets = structure  
muonevals   = truth  
muonledger  = reality  
```

👉 This is a complete autoresearch system.

---

# 🚀 Next Steps

- Add browser UI (WASM)
- Add visualization charts
- Add more puzzles dataset
