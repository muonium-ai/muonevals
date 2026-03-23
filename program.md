# Autoresearch: Sudoku Solver Optimization

## What this is

A Karpathy-style autoresearch loop applied to Sudoku solving.
Instead of optimizing a neural network's val_bpb, we optimize
a configurable Sudoku solver's composite score across a fixed
puzzle dataset.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  AUTORESEARCH LOOP                   │
│                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐   │
│  │ Mutate   │───>│ Evaluate │───>│ Keep/Revert  │   │
│  │ Config   │    │ Dataset  │    │ Best Config  │   │
│  └──────────┘    └──────────┘    └──────────────┘   │
│       ▲                               │             │
│       └───────────────────────────────┘             │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │              MUONLEDGER                        │   │
│  │  Every experiment → ledger transaction         │   │
│  │  Score/Steps/Time as double-entry postings     │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │              MUONTICKETS                       │   │
│  │  Tracks tickets for each phase of work         │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │              MUONEVALS                         │   │
│  │  Eval/Scorer/Runner framework for scoring      │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## The Mutable Part (like train.py)

`sudoku/config.py` — SolverConfig with 6 tunable knobs:

| Knob | Values | Effect |
|------|--------|--------|
| strategy | backtracking, heuristic, constraint | Solver backend |
| use_propagation | true/false | Propagate naked singles |
| propagation_depth | 0,1,2,3,5 | How many rounds (0=full) |
| candidate_ordering | ascending, descending, random, frequency | Value ordering |
| mrv | true/false | Minimum Remaining Values heuristic |
| max_steps | 10k, 50k, 100k | Safety abort limit |

## The Fixed Part (like prepare.py)

`sudoku/dataset.py` — 6 puzzles (2 easy, 2 medium, 2 hard).
Never modified. Ensures fair comparison across experiments.

## The Metric

Composite score (0–1): 60% correctness + 20% efficiency + 20% speed.
Lower steps + lower time + correct solution = higher score.

## The Loop

1. **Baseline**: Evaluate default SolverConfig on all 6 puzzles
2. **Mutate**: Change exactly one knob (isolate the variable)
3. **Evaluate**: Run on all 6 puzzles, compute mean score
4. **Compare**: If score > best → keep (accept). Else → revert (reject)
5. **Log**: Record to muonledger as a double-entry transaction
6. **Repeat**: Go to step 2

## Running

```bash
# Run 20 experiments (default)
python3 run_autoresearch.py

# Run 50 experiments with seed
python3 run_autoresearch.py --experiments 50 --seed 42

# Just see the summary
python3 run_autoresearch.py --experiments 10 --seed 42
```

## Outputs

- **Console**: Live experiment table showing each mutation and its effect
- **ledgers/*.ledger**: Double-entry accounting of every experiment
- **ledgers/*_results.tsv**: Tab-separated experiment log
- **Summary**: Final report with baseline → best improvement

## Key Insight

> muontickets = structure (what to work on)
> muonevals   = truth (did it actually improve?)
> muonledger  = reality (auditable record of every experiment)
