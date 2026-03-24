#!/usr/bin/env python3
"""CLI entrypoint for the Sudoku autoresearch loop.

Usage:
    python3 run_autoresearch.py                    # 20 experiments
    python3 run_autoresearch.py --experiments 50   # 50 experiments
    python3 run_autoresearch.py --seed 42          # reproducible
"""

import argparse
import sys

from sudoku.experiment import run_experiments
from sudoku.results import summary_table


def main():
    parser = argparse.ArgumentParser(
        description="Karpathy-style autoresearch for Sudoku solver optimization"
    )
    parser.add_argument(
        "--experiments", "-n", type=int, default=20,
        help="Number of experiments to run (default: 20)"
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--ticket-id", type=str, default="autoresearch",
        help="Ticket ID for ledger logging"
    )
    parser.add_argument(
        "--exploit", type=float, default=0.6,
        help="Fraction of exploit experiments (default: 0.6)"
    )
    parser.add_argument(
        "--explore", type=float, default=0.2,
        help="Fraction of explore experiments (default: 0.2)"
    )
    parser.add_argument(
        "--random", type=float, default=0.2,
        help="Fraction of random experiments (default: 0.2)"
    )
    parser.add_argument(
        "--workers", "-w", type=int, default=1,
        help="Parallel workers for experiment evaluation (default: 1, try 4-8 for speedup)"
    )
    args = parser.parse_args()

    print(f"Running {args.experiments} experiments...")
    print(f"Strategy mix: {args.exploit:.0%} exploit, {args.explore:.0%} explore, {args.random:.0%} random")
    if args.workers > 1:
        print(f"Workers: {args.workers}")
    if args.seed is not None:
        print(f"Seed: {args.seed}")
    print()

    run = run_experiments(
        num_experiments=args.experiments,
        seed=args.seed,
        ticket_id=args.ticket_id,
        exploit_pct=args.exploit,
        explore_pct=args.explore,
        random_pct=args.random,
        workers=args.workers,
    )

    # Print summary
    print()
    print(summary_table(run))


if __name__ == "__main__":
    main()
