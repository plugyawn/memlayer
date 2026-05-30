#!/usr/bin/env python3
import argparse
from pathlib import Path

from parse_loco_full_diagnostics import parse


def md(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4e}" if abs(value) < 0.01 or abs(value) >= 100 else f"{value:.4f}"
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--name", action="append", default=[])
    parser.add_argument("--case-contains", default="")
    args = parser.parse_args()

    names = set(args.name)
    rows = []
    for path in args.logs:
        rows.extend(parse(path)["precond"])

    if names:
        rows = [row for row in rows if row.get("name") in names]
    if args.case_contains:
        rows = [row for row in rows if args.case_contains in row.get("case", "")]

    columns = [
        "step",
        "case",
        "name",
        "layers",
        "blend",
        "delta_mean",
        "cos_mean",
        "ref_norm_mean",
        "ref_delta_mean",
        "ref_cos_mean",
    ]
    print("| " + " | ".join(columns) + " |")
    print("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        print("| " + " | ".join(md(row.get(col)) for col in columns) + " |")


if __name__ == "__main__":
    main()
