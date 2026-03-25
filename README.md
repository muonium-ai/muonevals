# muonevals

An evaluation framework for Karpathy-style autoresearch — iteratively optimizing solver algorithms through automated experimentation, composite scoring, and double-entry ledger tracking.

## What it does

Muonevals automates the loop of **mutate → evaluate → keep/revert → log** to search for better solver configurations. Instead of tuning `train.py` to minimize `val_bpb`, you tune a `SolverConfig` to maximize a composite Sudoku score across a fixed dataset.

The framework:

1. **Defines tunable knobs** — 6 parameters in `SolverConfig` (strategy, propagation, ordering, MRV, depth, step limit)
2. **Evaluates on a fixed dataset** — 6 Sudoku puzzles (2 easy, 2 medium, 2 hard) for fair comparison
3. **Computes a composite score** — `0.6 × correctness + 0.2 × efficiency + 0.2 × speed`
4. **Runs an autoresearch loop** — three search modes (exploit, explore, random) with configurable mix
5. **Tracks results** — all-time best/worst in version-controlled TSV files, every experiment logged to a double-entry ledger via [muonledger](https://github.com/muonium-ai/muonledger)

## Project structure

```
muonevals/          Core evaluation framework (Eval, scorers, runner, ledger, tickets, reports)
sudoku/             Sudoku solver domain (solvers, config, dataset, experiment loop, results)
tests/              Test suite (16 files)
ledgers/            Experiment output (.ledger files, _results.tsv)
run_autoresearch.py CLI entrypoint
```

## Quick start

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Run 20 experiments (default)
uv run python run_autoresearch.py

# Run 200 experiments with reproducible seed and 4 workers
uv run python run_autoresearch.py --experiments 200 --seed 42 -w 4

# Custom search strategy mix
uv run python run_autoresearch.py --exploit 0.4 --explore 0.3 --random 0.3
```

## The 6 tunable knobs

| Knob | Values | Default |
|------|--------|---------|
| `strategy` | backtracking, heuristic, constraint | constraint |
| `use_propagation` | true, false | true |
| `propagation_depth` | 0 (unlimited), 1, 2, 3, 5 | 0 |
| `candidate_ordering` | ascending, descending, random, frequency | ascending |
| `mrv` | true, false | true |
| `max_steps` | 10000, 50000, 100000 | 50000 |

## Search modes

- **Exploit** (default 60%) — mutate one knob from current best to isolate its effect
- **Explore** (default 20%) — switch strategy and randomize 2–3 knobs to escape local optima
- **Random** (default 20%) — fully randomize all knobs for serendipitous discovery

## Makefile targets

```bash
make test           # Run pytest
make autoresearch   # 200 experiments, seed 42, 4 workers
make explore        # 200 experiments, explore-heavy (60%)
make random         # 200 experiments, random-heavy (60%)
make all            # Run explore and random in parallel
```

## Core library (`muonevals/`)

| Module | Purpose |
|--------|---------|
| `eval.py` | `Eval` class — wraps a scorer function, validates output in [0, 1] |
| `runner.py` | `run_eval()` — evaluates an agent across a dataset, returns mean score |
| `scorers.py` | Built-in scorers: `correctness()`, `efficiency()`, `speed()` |
| `ledger.py` | `EvalLedger` — double-entry ledger for recording eval runs |
| `ticket.py` | `EvalTicket` — tracks a goal with multiple attempts and a target score |
| `export.py` | `export_eval_run()` — run all strategies and save to ledger file |
| `reports.py` | `balance_report()`, `register_report()` — muonledger reporting |

## Dependencies

- Python >= 3.11
- [muonledger](https://github.com/muonium-ai/muonledger) (included as git submodule)
- [muontickets](https://github.com/muonium-ai/muontickets) (included as git submodule)
- pytest (dev)
