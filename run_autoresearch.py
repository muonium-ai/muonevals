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
from sudoku.results import results_to_tsv, save_results_tsv, summary_table


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
    args = parser.parse_args()

    print(f"Running {args.experiments} experiments...")
    if args.seed is not None:
        print(f"Seed: {args.seed}")
    print()

    run = run_experiments(
        num_experiments=args.experiments,
        seed=args.seed,
        ticket_id=args.ticket_id,
    )

    # Save results
    tsv_path = save_results_tsv(run)

    # Print summary
    print()
    print(summary_table(run))
    print(f"\nResults saved: {tsv_path}")


if __name__ == "__main__":
    main()
