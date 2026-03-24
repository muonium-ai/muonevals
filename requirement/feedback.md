# Feedback: Muon Autoresearch Sudoku

Date: 2026-03-24

Scope reviewed:
- `requirement/muon_autoresearch_sudoku.md`
- `run_autoresearch.py`
- `muonevals/*`
- `sudoku/*`
- targeted tests under `tests/`

Validation run:
- `uv run pytest tests/test_eval.py tests/test_scorers.py tests/test_runner.py tests/test_ledger.py tests/test_dataset.py tests/test_sudoku.py tests/test_strategies.py tests/test_evaluate.py tests/test_configurable_solver.py tests/test_experiment.py tests/test_results.py tests/test_ticket.py`
- Result: 94 passed in 49.21s

## Overall

The repo already covers the four phases in broad strokes: base evals exist, ticket and ledger support exist, multiple Sudoku solvers exist, and there is an experiment loop. The main problem is not missing surface area. It is drift between the requirement and what the code actually guarantees.

## Findings

### 1. Critical: `SolverConfig.strategy` is logged, mutated, and optimized, but it does not change solver behavior

References:
- `sudoku/config.py:29`
- `sudoku/configurable_solver.py:114`
- `sudoku/experiment.py:215`

Why this matters:
- MT-009 and MT-010 describe real strategy variants: `backtracking`, `heuristic`, `constraint`.
- The experiment loop treats `strategy` as an optimization knob.
- `solve_with_config()` never reads `config.strategy`, so the reported backend is effectively cosmetic.

Observed behavior:
- Running the same puzzle with identical non-strategy knobs produced the same outcome for all three strategies:
- `backtracking True 1 0.175`
- `heuristic True 1 0.175`
- `constraint True 1 0.189`

Impact:
- Experiment results can claim a backend change that never happened.
- `best.tsv` entries can attribute wins to the wrong strategy.
- Phase 4 conclusions are not trustworthy until this is fixed.

Recommended fix:
- Either make `strategy` select a distinct solving path, or remove it from `SolverConfig` and keep backend comparison separate from config mutation.

### 2. High: strategy mix percentages are not honored and are not validated

References:
- `run_autoresearch.py:33`
- `sudoku/experiment.py:106`

Why this matters:
- The CLI exposes `--exploit`, `--explore`, and `--random` as exact fractions.
- `_build_strategy_schedule()` forces at least one `explore` and one `random` run when there are at least 3 experiment slots, even when the caller asked for `0.0`.
- It also allows totals greater than 100%, which can produce a schedule longer than the requested run.

Observed behavior:
- `_build_strategy_schedule(10, 1.0, 0.0, 0.0)` still yields 1 `explore` and 1 `random`.
- `_build_strategy_schedule(10, 0.2, 0.8, 0.8)` yields 14 scheduled items for 9 non-baseline slots.

Impact:
- The CLI lies about what run will actually execute.
- Reproducibility and result interpretation are weaker than they look.

Recommended fix:
- Validate that each percentage is in `[0, 1]`.
- Validate that the total is `1.0` or normalize explicitly.
- Do not force non-zero counts when the caller requested zero.

### 3. High: best-result commit flow can report success even when the git commit failed

References:
- `sudoku/best.py:99`
- `sudoku/best.py:128`
- `sudoku/experiment.py:183`
- `sudoku/experiment.py:239`

Why this matters:
- `commit_best()` writes `best.tsv` before attempting `git commit`.
- `check_and_commit()` returns `True` whenever the score improved, even if `commit_best()` returned `None`.
- The caller prints `"committed to git"` based on that boolean.

Impact:
- Console output can claim a commit happened when it did not.
- A normal evaluation run can mutate `best.tsv` as a side effect.
- This is risky in tests, CI, or a dirty worktree.

Recommended fix:
- Return commit success from `check_and_commit()` based on the real `commit_best()` result.
- Separate "persist best locally" from "create git commit".
- Consider making auto-commit opt-in instead of default.

### 4. Medium: the built-in scorers do not match the requirement contract

References:
- `requirement/muon_autoresearch_sudoku.md:45`
- `muonevals/scorers.py:4`

Why this matters:
- MT-002 explicitly defines `correctness(solution)` in terms of `is_valid(solution)`.
- The implementation uses plain truthiness: any non-empty object gets `1.0`.
- `efficiency()` and `speed()` also accept negative inputs and can return values greater than `1.0`, which violates the "normalized" acceptance criterion.

Observed behavior:
- `correctness([0]) == 1.0`
- `efficiency(-0.5) == 2.0`
- `speed(-0.5) == 2.0`

Impact:
- Phase 1 is not actually implementing the stated scoring semantics.
- The current tests lock in the wrong behavior instead of catching it.

Recommended fix:
- Make `correctness()` validate the actual structure it scores.
- Reject negative `steps` and `time_ms`, or clamp them before scoring.
- Update tests to match the contract from the requirement.

### 5. Medium: `Attempt.passed` is not compatible with target-based tickets

References:
- `requirement/muon_autoresearch_sudoku.md:83`
- `muonevals/ticket.py:19`

Why this matters:
- Tickets are defined by `target_score`.
- `Attempt.passed` hardcodes `score >= 1.0`, which means a score of `0.95` would not count as passed even for a ticket whose target is `0.95`.

Impact:
- The API is misleading.
- If any caller starts using `Attempt.passed`, it will produce incorrect ticket status.

Recommended fix:
- Remove `Attempt.passed`, or move pass/fail logic to `EvalTicket` where `target_score` is available.

## Requirement Gaps

### 1. The target score in the requirement is not calibrated to the current scoring system

Reference:
- `requirement/muon_autoresearch_sudoku.md:85`
- `best.tsv:10`

Notes:
- The sample ticket sets `target_score: 0.95`.
- The current repo's best recorded score is `0.7261`.
- With the current combined scoring approach, `0.95` looks aspirational rather than actionable.

Recommendation:
- Replace fixed targets with either:
- a baseline-plus-delta target
- a percentile target across the dataset
- or a target derived from the actual score range for this evaluation

### 2. The requirement mixes two different meanings of "strategy"

Reference:
- `requirement/muon_autoresearch_sudoku.md:155`
- `sudoku/strategies.py:9`
- `sudoku/config.py:29`

Notes:
- In the requirement, `strategy` means one of three solver backends.
- In the implementation, there is both a strategy registry and a mutable config object with many other knobs.
- The result is conceptual overlap and implementation drift.

Recommendation:
- Decide whether Phase 4 is:
- backend selection across named solvers
- parameter search within one configurable solver
- or a two-level search that evaluates both separately

### 3. Acceptance criteria are too weak for auditing and reproducibility

Examples:
- MT-005 only says "Every run recorded".
- MT-010 does not define the scoring formula.
- MT-011 does not define what "mutate" is allowed to change.

Recommendation:
- Add explicit acceptance criteria for:
- ledger fields and storage location
- deterministic runs under a fixed seed
- expected dataset size and puzzle set
- how search-mix percentages should behave

## Missing or Incorrect Tests

The current suite is solid for the happy path, but it does not protect the highest-risk behaviors.

Missing tests:
- `config.strategy` must materially change solver execution.
- zero-percent `explore` or `random` should remain zero.
- invalid percentage totals should raise.
- failed git commit should not be reported as committed.
- negative inputs to `efficiency()` and `speed()` should be rejected.
- `correctness()` should reject structurally invalid but truthy solutions.
- ticket pass/fail semantics should be tested against `target_score`.

Incorrect tests today:
- `tests/test_scorers.py` treats any truthy solution as correct, which codifies the current bug instead of the requirement.

## Recommended Order of Work

1. Fix the non-functional `strategy` knob or remove it.
2. Tighten the search-mix input contract and schedule generation.
3. Make best-result persistence and git commits truthful and side-effect safe.
4. Bring scorers and scorer tests back in line with the requirement.
5. Rewrite the requirement so the target score, strategy model, and acceptance criteria match the actual architecture.
