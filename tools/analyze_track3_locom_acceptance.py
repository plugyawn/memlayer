#!/usr/bin/env python3
"""Reconstruct LocoProp-M accepted-layer sets from kdiag logs.

This answers a different question from per-layer medians:

    when the run says "all layers", which c_fc layers actually get corrections?

The generated Track 3 code stores a correction only when the local loss improves
and the correction cosine clears `min_cos_desc`.  The kdiag rows contain the same
loss ratio and cosine for the logged K values, so we can reconstruct the gate:

    accepted ~= ratio < 1 and cos >= min_cos

`locoprop_m_apply` rows do not include layer ids and are truncated to the first
eight entries, so this script compares only counts and marks capped apply rows.
"""

from __future__ import annotations

import argparse
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


KDIAG_RE = re.compile(r"locoprop_m_kdiag step=(?P<step>\d+)\s+l(?P<layer>\d+)\s+(?P<body>.*)")
ITEM_RE = re.compile(r"k(?P<k>\d+):(?P<body>[^|]+)")
KV_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([+-]?(?:inf|nan|[0-9.eE+-]+))", re.IGNORECASE)
APPLY_STEP_RE = re.compile(r"locoprop_m_apply step=(?P<step>\d+) ")
APPLY_ENTRY_RE = re.compile(r"shape=\(")


@dataclass(frozen=True)
class KDiag:
    step: int
    layer: int
    k: int
    ratio: float
    cos: float
    cos_text: str


def _float(text: str, default: float = float("nan")) -> float:
    try:
        return float(text)
    except ValueError:
        return default


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _name(path: Path) -> str:
    stem = path.stem
    for prefix in ("track3_kdepth_", "track3_prefix_", "track3_layersubset_"):
        stem = stem.removeprefix(prefix)
    return re.sub(r"_seed\d+$", "", stem)


def _collect_paths(entries: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for entry in entries:
        if entry.is_dir():
            paths.extend(sorted(entry.glob("*.log")))
        else:
            paths.append(entry)
    return [path for path in paths if path.exists()]


def _steps_from(text: str, rows: list[KDiag]) -> list[int]:
    if text:
        return [int(item) for item in text.split(",") if item.strip()]
    return sorted({row.step for row in rows})


def parse_log(path: Path) -> tuple[list[KDiag], dict[int, int]]:
    rows: list[KDiag] = []
    apply_counts: dict[int, int] = {}
    for line in path.read_text(errors="replace").splitlines():
        if match := KDIAG_RE.search(line):
            step = int(match["step"])
            layer = int(match["layer"])
            for item in ITEM_RE.finditer(match["body"]):
                raw_values = dict(KV_RE.findall(item["body"]))
                values = {key: _float(value) for key, value in raw_values.items()}
                rows.append(
                    KDiag(
                        step=step,
                        layer=layer,
                        k=int(item["k"]),
                        ratio=values.get("ratio", float("nan")),
                        cos=values.get("cos", float("nan")),
                        cos_text=raw_values.get("cos", "nan"),
                    )
                )
            continue
        if step_match := APPLY_STEP_RE.search(line):
            apply_counts[int(step_match["step"])] = len(APPLY_ENTRY_RE.findall(line))
    return rows, apply_counts


def _accepted_layers(rows: list[KDiag], *, step: int, k: int, min_cos: float) -> list[int]:
    accepted = []
    for row in rows:
        if row.step != step or row.k != k:
            continue
        if not (math.isfinite(row.ratio) and math.isfinite(row.cos) and row.ratio < 1.0):
            continue
        # kdiag prints three decimals. A textual "-0.000" can come from a small
        # negative full-precision cosine that the real gate rejected.
        cos_ok = row.cos >= min_cos
        if min_cos == 0.0 and row.cos == 0.0 and row.cos_text.startswith("-"):
            cos_ok = False
        if cos_ok:
            accepted.append(row.layer)
    return sorted(accepted)


def _set_text(layers: list[int]) -> str:
    return ",".join(str(layer) for layer in layers) if layers else "-"


def print_report(paths: list[Path], *, k: int, steps_text: str, min_cos: float, apply_log_cap: int) -> None:
    print("# Track 3 LocoProp-M Accepted-Layer Sequence")
    print()
    print(
        "Gate reconstruction: `accepted ~= loss/loss0 < 1 and cos >= min_cos`. "
        f"Apply rows are layerless and logged with cap `{apply_log_cap}`."
    )
    print()

    for path in paths:
        rows, apply_counts = parse_log(path)
        steps = _steps_from(steps_text, rows)
        print(f"## {_name(path)}")
        print()
        print(f"- file: `{path}`")
        print(f"- K: `{k}`")
        print(f"- min_cos: `{min_cos}`")
        print()
        print("| step | accepted count | accepted layers | logged apply count | count check |")
        print("| ---: | ---: | --- | ---: | --- |")
        freq: Counter[int] = Counter()
        sets: Counter[tuple[int, ...]] = Counter()
        mismatches = 0
        for step in steps:
            accepted = _accepted_layers(rows, step=step, k=k, min_cos=min_cos)
            if not accepted and not any(row.step == step and row.k == k for row in rows):
                continue
            apply_count = apply_counts.get(step)
            for layer in accepted:
                freq[layer] += 1
            sets[tuple(accepted)] += 1
            expected_logged = min(len(accepted), apply_log_cap)
            if apply_count is None:
                check = "missing apply"
            elif apply_count == expected_logged:
                check = "ok" if len(accepted) <= apply_log_cap else "ok capped"
            else:
                check = f"mismatch expected {expected_logged}"
                mismatches += 1
            print(
                f"| {step} | {len(accepted)} | {_set_text(accepted)} | "
                f"{apply_count if apply_count is not None else 'nan'} | {check} |"
            )
        print()
        print("Layer acceptance frequency:")
        print()
        print("| layer | frequency |")
        print("| ---: | ---: |")
        total_steps = sum(sets.values())
        for layer in sorted(freq):
            print(f"| {layer} | {_fmt(freq[layer] / max(total_steps, 1), 2)} |")
        print()
        common_set, common_count = sets.most_common(1)[0] if sets else ((), 0)
        print("Read:")
        print(f"- most common accepted set: `{_set_text(list(common_set))}` ({common_count}/{total_steps} logged steps)")
        print(f"- count mismatches against apply log: `{mismatches}`")
        if mismatches:
            print("- investigate count mismatches before relying on the gate reconstruction.")
        elif total_steps:
            print("- gate reconstruction matches the layerless apply-count trace within the logging cap.")
        print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--steps", default="")
    parser.add_argument("--min-cos", type=float, default=0.0)
    parser.add_argument("--apply-log-cap", type=int, default=8)
    args = parser.parse_args()

    print_report(
        _collect_paths(args.logs),
        k=args.k,
        steps_text=args.steps,
        min_cos=args.min_cos,
        apply_log_cap=args.apply_log_cap,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
