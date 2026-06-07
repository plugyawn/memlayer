#!/usr/bin/env python3
"""Estimate whether a LocoProp-M correction can matter by scaling alone.

The K-step local solve can look healthy while the applied correction is both
small and nearly orthogonal to the base Muon step.  This report converts logged
`locoprop_m_kdiag` and `locoprop_m_apply` rows into a scale budget:

    aligned_fraction ~= (effective correction norm / base step norm) * cos

Then it asks how much extra alpha would be required to contribute a chosen
base-step-aligned fraction.  If that alpha implies a total correction norm near
or above one full Muon step, "just scale it up" is not a plausible fix.
"""

from __future__ import annotations

import argparse
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import median


KDIAG_RE = re.compile(r"locoprop_m_kdiag step=(?P<step>\d+)\s+l(?P<layer>\d+)\s+(?P<body>.*)")
ITEM_RE = re.compile(r"k(?P<k>\d+):(?P<body>[^|]+)")
KV_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([+-]?(?:inf|nan|[0-9.eE+-]+))", re.IGNORECASE)
APPLY_STEP_RE = re.compile(r"locoprop_m_apply step=(?P<step>\d+) ")
APPLY_ENTRY_RE = re.compile(
    r"base_step=(?P<base>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r",corr_norm=(?P<corr>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r",cap=(?P<cap>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r",scale=(?P<scale>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)",
    re.IGNORECASE,
)


def _name(path: Path) -> str:
    stem = path.stem
    for prefix in ("track3_kdepth_", "track3_from2000_", "track3_locom_2000_", "track3_prefix_"):
        stem = stem.removeprefix(prefix)
    return stem.removesuffix("_seed3710")


def _finite(values: list[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def _median(values: list[float]) -> float | None:
    values = _finite(values)
    return None if not values else float(median(values))


def _float(text: str) -> float:
    try:
        return float(text)
    except ValueError:
        return float("nan")


def _fmt(value: float | None, digits: int = 4) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _fmt_x(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.1f}x"


def parse_log(path: Path) -> tuple[dict[tuple[int, int], list[float]], dict[int, list[float]]]:
    cos_by_step_k: dict[tuple[int, int], list[float]] = defaultdict(list)
    eff_by_step: dict[int, list[float]] = defaultdict(list)
    for line in path.read_text(errors="replace").splitlines():
        if match := KDIAG_RE.search(line):
            step = int(match["step"])
            for item in ITEM_RE.finditer(match["body"]):
                values = {key: _float(value) for key, value in KV_RE.findall(item["body"])}
                cos_by_step_k[(step, int(item["k"]))].append(values.get("cos", float("nan")))
            continue
        if step_match := APPLY_STEP_RE.search(line):
            step = int(step_match["step"])
            for entry in APPLY_ENTRY_RE.finditer(line):
                base = _float(entry["base"])
                corr = _float(entry["corr"])
                scale = _float(entry["scale"])
                if math.isfinite(base) and math.isfinite(corr) and math.isfinite(scale) and base > 0:
                    eff_by_step[step].append((corr * scale) / base)
    return cos_by_step_k, eff_by_step


def print_report(
    paths: list[Path],
    *,
    steps: set[int] | None,
    ks: set[int],
    targets: list[float],
) -> None:
    target_headers = []
    for target in targets:
        pct = int(round(target * 100))
        target_headers.extend([f"alpha for {pct}% aligned", "total norm then"])

    print("# Track 3 LocoProp-M Tick Budget")
    print()
    print(
        "| log | step | k | eff/base med | cos med | aligned frac | "
        + " | ".join(target_headers)
        + " |"
    )
    print("| --- | ---: | ---: | ---: | ---: | ---: | " + " | ".join("---:" for _ in target_headers) + " |")

    for path in paths:
        cos_by_step_k, eff_by_step = parse_log(path)
        for (step, k), cosines in sorted(cos_by_step_k.items()):
            if steps is not None and step not in steps:
                continue
            if k not in ks or step not in eff_by_step:
                continue
            eff = _median(eff_by_step[step])
            cos = _median(cosines)
            aligned = None if eff is None or cos is None else eff * cos
            cells = []
            for target in targets:
                if aligned is None or not math.isfinite(aligned) or aligned <= 0 or eff is None:
                    cells.extend(["nan", "nan"])
                else:
                    alpha = target / aligned
                    cells.extend([_fmt_x(alpha), _fmt(alpha * eff, 2) + "x"])
            print(
                f"| {_name(path)} | {step} | {k} | {_fmt(eff)} | {_fmt(cos)} | "
                f"{_fmt(aligned, 6)} | " + " | ".join(cells) + " |"
            )

    print()
    print("Read: `total norm then` is the total LocoProp correction norm as a multiple of the base Muon step.")
    print("Large alpha with total norm near or above `1x` means scaling would create a major sideways perturbation.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--steps", default="")
    parser.add_argument("--ks", default="5,8,10")
    parser.add_argument("--targets", default="0.01,0.05")
    args = parser.parse_args()

    steps = {int(item) for item in args.steps.split(",") if item.strip()} if args.steps else None
    ks = {int(item) for item in args.ks.split(",") if item.strip()}
    targets = [float(item) for item in args.targets.split(",") if item.strip()]
    print_report(args.logs, steps=steps, ks=ks, targets=targets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
