#!/usr/bin/env python3
"""QFF 2026 Phase 2 (PS-P2) - Enterprise Cryptographic Inventory & Migration Planner.

Official CLI Tool for Judging and Execution.

Usage:
    python run_inventory.py --input <inventory.csv> --output <predictions.csv>

Standard library only. Runs completely offline.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.classifier import classify_record
from src.prioritizer import prioritize_inventory

OUTPUT_COLUMNS = [
    "asset_id",
    "predicted_label",
    "priority_score",
    "priority_rank",
    "recommended_action",
    "migration_wave",
    "depends_on",
    "rationale",
]


def process_inventory(input_path: Path | str, output_path: Path | str) -> int:
    """Ingests inventory CSV, classifies every record, and produces predictions CSV."""
    t0 = time.perf_counter()
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        print(f"Error: input file '{input_file}' not found.", file=sys.stderr)
        return 1

    with open(input_file, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)

    if not records:
        print(f"Warning: input file '{input_file}' contains no records.", file=sys.stderr)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
        return 0

    # Step 1: Classify all records
    labels = [classify_record(r) for r in records]

    # Step 2: Prioritize, score, rank, and map migration actions
    predictions = prioritize_inventory(records, labels)

    # Step 3: Write predictions CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(predictions)

    elapsed = time.perf_counter() - t0
    print(f"Successfully processed {len(records)} records in {elapsed:.3f}s.")
    print(f"Predictions written to: {output_file}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PS-P2 Enterprise Cryptographic Inventory and Migration Planner"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input inventory CSV (e.g. inventory_dev.csv)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output predictions CSV (e.g. predictions.csv)",
    )
    args = parser.parse_args()
    return process_inventory(args.input, args.output)


if __name__ == "__main__":
    sys.exit(main())
