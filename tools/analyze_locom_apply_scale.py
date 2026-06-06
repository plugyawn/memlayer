#!/usr/bin/env python3
"""Summarize LocoProp-M apply-scale logs.

The `locoprop_m_apply` row logs the base Muon step norm, the raw LocoProp
correction norm, and the scale actually applied. This script reports the raw
and effective correction fractions relative to the base step.
"""

from __future__ import annotations

import argparse
import math
import re
import statistics
from pathlib import Path


STEP_RE = re.compile(r"locoprop_m_apply step=(\d+) ")
ENTRY_RE = re.compile(
    r"base_step=(?P<base>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r",corr_norm=(?P<corr>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r",cap=(?P<cap>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r",scale=(?P<scale>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)",
    re.IGNORECASE,
)


def _finite_float(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def _fmt(value: float | None) -> str:
    if value is None:
        return "nan"
    return f"{value:.4g}"


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _p90(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, math.ceil(0.9 * len(ordered)) - 1)
    return ordered[idx]


def parse_log(path: Path) -> dict[int, list[tuple[float, float, float, float]]]:
    by_step: dict[int, list[tuple[float, float, float, float]]] = {}
    for line in path.read_text(errors="replace").splitlines():
        step_match = STEP_RE.search(line)
        if not step_match:
            continue
        step = int(step_match.group(1))
        entries: list[tuple[float, float, float, float]] = []
        for match in ENTRY_RE.finditer(line):
            base = _finite_float(match.group("base"))
            corr = _finite_float(match.group("corr"))
            cap = _finite_float(match.group("cap"))
            scale = _finite_float(match.group("scale"))
            if base is None or corr is None or cap is None or scale is None:
                continue
            if base <= 0:
                continue
            entries.append((base, corr, cap, scale))
        if entries:
            by_step.setdefault(step, []).extend(entries)
    return by_step


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    args = parser.parse_args()

    print("| log | step | n | base_med | raw_frac_med | raw_frac_p90 | scale_med | eff_frac_med | eff_frac_p90 | cap |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for path in args.logs:
        by_step = parse_log(path)
        for step in sorted(by_step):
            entries = by_step[step]
            bases = [base for base, _, _, _ in entries]
            raw_fracs = [corr / base for base, corr, _, _ in entries]
            scales = [scale for _, _, _, scale in entries]
            eff_fracs = [(corr * scale) / base for base, corr, _, scale in entries]
            caps = [cap for _, _, cap, _ in entries]
            print(
                f"| {path.name} | {step} | {len(entries)}"
                f" | {_fmt(_median(bases))}"
                f" | {_fmt(_median(raw_fracs))}"
                f" | {_fmt(_p90(raw_fracs))}"
                f" | {_fmt(_median(scales))}"
                f" | {_fmt(_median(eff_fracs))}"
                f" | {_fmt(_p90(eff_fracs))}"
                f" | {_fmt(_median(caps))} |"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
