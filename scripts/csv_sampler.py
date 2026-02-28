"""
CSV Sampler - Sample n records from a CSV file.

Usage:
    py -m csv_sampler input.csv
    py -m csv_sampler input.csv -n 25
    py -m csv_sampler input.csv -n 50 -o output.csv
    py -m csv_sampler input.csv --seed 42
"""

import argparse
import csv
import random
import sys
from pathlib import Path


def sample_csv(
    input_path: str, n: int = 10, output_path: str = None, seed: int = None
) -> str:
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = input_file.stem + "_sample" + input_file.suffix

    with open(input_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    total = len(rows)
    if n > total:
        print(
            f"Warning: requested {n} samples but file only has {total} records. Returning all records."
        )
        n = total

    if seed is not None:
        random.seed(seed)

    sampled = random.sample(rows, n)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sampled)

    print(f"Sampled {n}/{total} records → {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Sample n records from a CSV file.",
        epilog="Example: py -m csv_sampler data.csv -n 25 -o sampled.csv",
    )
    parser.add_argument("input", help="Path to the input CSV file")
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=10,
        metavar="N",
        help="Number of records to sample (default: 10)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="FILE",
        help="Path for the output CSV file (default: <input>_sample.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )

    args = parser.parse_args()

    try:
        sample_csv(args.input, n=args.count, output_path=args.output, seed=args.seed)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


# # Basic usage (samples 10 records by default)
# py -m csv_sampler data.csv

# # Sample 25 records
# py -m csv_sampler data.csv -n 25

# # Specify output file
# py -m csv_sampler data.csv -n 50 -o my_sample.csv

# # Reproducible sample with a seed
# py -m csv_sampler data.csv -n 20 --seed 42
