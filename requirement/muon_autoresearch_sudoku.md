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
  target_score: 0.95
```

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
- Every run recorded

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

## 🎫 Ticket MT-009: Strategy Variants

```python
strategies = [
    "backtracking",
    "heuristic",
    "constraint"
]
```

---

## 🎫 Ticket MT-010: Evaluate Strategies

```python
results = []
for s in strategies:
    solution, steps, time = solve(grid, s)
    score = evaluate(solution, steps, time)
    results.append((s, score))

best = max(results, key=lambda x: x[1])
```

---

## 🎫 Ticket MT-011: Improvement Loop

```python
for i in range(10):
    strategy = mutate(best)
    score = evaluate(strategy)
```

---

# 🚀 Output Example

| Strategy | Steps | Time | Score |
|----------|------:|-----:|------:|
| Basic | 500 | 120ms | 0.62 |
| Heuristic | 200 | 60ms | 0.78 |
| Constraint | 80 | 30ms | 0.91 |

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
