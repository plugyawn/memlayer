#!/usr/bin/env python3
"""Join LocoProp-M validation, local-objective, and apply-scale diagnostics.

This is the compact "what makes it tick?" analyzer.  The separate tools answer
individual questions:

* analyze_locom_k_effect.py: where is the local K knee?
* analyze_track3_locom_window_health.py: when does validation slope go cold?
* analyze_track3_locom_suffix_probe.py: which suffix lane wins?

This script combines the ingredients per log/step so we can see whether a
validation phase has:

* local objective improvement for K=5-10,
* non-random directional structure in cosines,
* an actually applied correction at a meaningful fraction of the base step,
* and an external validation slope consistent with the target.
"""

from __future__ import annotations

import argparse
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median


VAL_RE = re.compile(r"step:(?P<step>\d+)/\d+\s+val_loss:(?P<loss>[0-9.]+)")
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
HEADER_RE = re.compile(
    r"LocoM enabled=(?P<enabled>\w+).*?"
    r"local_opt=(?P<local_opt>\S+).*?"
    r"random_correction=(?P<random>\w+).*?"
    r"correction_mode=(?P<mode>\S+).*?"
    r"norm_target=(?P<norm_target>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
)


@dataclass
class KRow:
    layer: int
    k: int
    ratio: float
    corr_norm: float
    cos: float


@dataclass
class ApplySummary:
    count: int = 0
    base_med: float | None = None
    raw_frac_med: float | None = None
    eff_frac_med: float | None = None
    eff_frac_p90: float | None = None
    scale_med: float | None = None


@dataclass
class LogData:
    path: Path
    name: str
    vals: dict[int, float] = field(default_factory=dict)
    krows: dict[int, list[KRow]] = field(default_factory=lambda: defaultdict(list))
    apply: dict[int, ApplySummary] = field(default_factory=dict)
    enabled: str | None = None
    local_opt: str | None = None
    random: str | None = None
    mode: str | None = None
    norm_target: float | None = None


def _float(text: str, default: float = float("nan")) -> float:
    try:
        return float(text)
    except ValueError:
        return default


def _finite(values: list[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def _median(values: list[float]) -> float | None:
    values = _finite(values)
    return None if not values else float(median(values))


def _p90(values: list[float]) -> float | None:
    values = sorted(_finite(values))
    if not values:
        return None
    index = min(len(values) - 1, math.ceil(0.9 * len(values)) - 1)
    return float(values[index])


def _fmt(value: float | None, digits: int = 5) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _fmt_sci(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.3e}"


def _name(path: Path) -> str:
    stem = path.stem
    for prefix in (
        "track3_kdepth_",
        "track3_from2000_",
        "track3_survival_",
        "track3_locom_2000_",
        "track3_prefix_",
    ):
        stem = stem.removeprefix(prefix)
    return stem.removesuffix("_seed3710")


def _collect_paths(entries: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for entry in entries:
        if entry.is_dir():
            paths.extend(sorted(entry.glob("*.log")))
        else:
            paths.append(entry)
    return [path for path in paths if path.exists()]


def parse_log(path: Path) -> LogData:
    data = LogData(path=path, name=_name(path))
    apply_entries: dict[int, list[tuple[float, float, float]]] = defaultdict(list)
    for line in path.read_text(errors="replace").splitlines():
        if match := VAL_RE.search(line):
            data.vals[int(match["step"])] = float(match["loss"])
            continue
        if match := HEADER_RE.search(line):
            data.enabled = match["enabled"]
            data.local_opt = match["local_opt"]
            data.random = match["random"]
            data.mode = match["mode"]
            data.norm_target = _float(match["norm_target"])
            continue
        if match := KDIAG_RE.search(line):
            step = int(match["step"])
            layer = int(match["layer"])
            for item in ITEM_RE.finditer(match["body"]):
                values = {key: _float(value) for key, value in KV_RE.findall(item["body"])}
                data.krows[step].append(
                    KRow(
                        layer=layer,
                        k=int(item["k"]),
                        ratio=values.get("ratio", float("nan")),
                        corr_norm=values.get("corr_norm", float("nan")),
                        cos=values.get("cos", float("nan")),
                    )
                )
            continue
        if step_match := APPLY_STEP_RE.search(line):
            step = int(step_match["step"])
            for entry in APPLY_ENTRY_RE.finditer(line):
                base = _float(entry["base"])
                corr = _float(entry["corr"])
                scale = _float(entry["scale"])
                if math.isfinite(base) and math.isfinite(corr) and math.isfinite(scale) and base > 0:
                    apply_entries[step].append((base, corr / base, (corr * scale) / base))
    for step, entries in apply_entries.items():
        bases = [base for base, _, _ in entries]
        raw_fracs = [raw for _, raw, _ in entries]
        eff_fracs = [eff for _, _, eff in entries]
        scales = [eff / raw for raw, eff in zip(raw_fracs, eff_fracs) if raw > 0]
        data.apply[step] = ApplySummary(
            count=len(entries),
            base_med=_median(bases),
            raw_frac_med=_median(raw_fracs),
            eff_frac_med=_median(eff_fracs),
            eff_frac_p90=_p90(eff_fracs),
            scale_med=_median(scales),
        )
    return data


def _steps_from(text: str, logs: list[LogData]) -> list[int]:
    if text:
        return [int(item) for item in text.split(",") if item.strip()]
    steps: set[int] = set()
    for log in logs:
        steps.update(log.vals)
        steps.update(log.krows)
        steps.update(log.apply)
    return sorted(steps)


def _target_ratio(vals: dict[int, float], start: int, end: int, target_step: int, target_loss: float) -> float | None:
    if start not in vals or end not in vals or end <= start or target_step <= start:
        return None
    needed = (vals[start] - target_loss) / (target_step - start)
    if needed <= 0:
        return None
    actual = (vals[start] - vals[end]) / (end - start)
    return actual / needed


def _summarize_k(rows: list[KRow], k: int) -> tuple[int, float | None, float | None, float | None, int, int, int]:
    selected = [row for row in rows if row.k == k]
    if not selected:
        return 0, None, None, None, 0, 0, 0
    ratios = [row.ratio for row in selected]
    corrs = [row.corr_norm for row in selected]
    cosines = [row.cos for row in selected]
    return (
        len(selected),
        _median(ratios),
        _median(corrs),
        _median(cosines),
        sum(1 for value in ratios if math.isfinite(value) and value < 1.0),
        sum(1 for value in cosines if math.isfinite(value) and value >= 0.0),
        sum(1 for value in cosines if math.isfinite(value) and value < 0.0),
    )


def _print_validation(logs: list[LogData], steps: list[int], target_step: int, target_loss: float) -> None:
    print("## Validation And Slope")
    print()
    print("| log | " + " | ".join(str(step) for step in steps if any(step in log.vals for log in logs)) + " |")
    print("| --- | " + " | ".join("---:" for step in steps if any(step in log.vals for log in logs)) + " |")
    val_steps = [step for step in steps if any(step in log.vals for log in logs)]
    for log in logs:
        print(f"| {log.name} | " + " | ".join(_fmt(log.vals.get(step)) for step in val_steps) + " |")
    print()
    print("| log | window | slope/needed | status |")
    print("| --- | --- | ---: | --- |")
    for log in logs:
        for start, end in zip(val_steps, val_steps[1:]):
            ratio = _target_ratio(log.vals, start, end, target_step, target_loss)
            if ratio is None:
                continue
            status = "healthy" if ratio >= 1.0 else "marginal" if ratio >= 0.9 else "cold"
            print(f"| {log.name} | {start}->{end} | {_fmt(ratio, 2)}x | {status} |")
    print()


def _print_k(logs: list[LogData], steps: list[int], ks: list[int]) -> None:
    print("## Local Objective And Direction")
    print()
    print("| log | step | k | layers | med loss/loss0 | med corr_norm | med cos | good loss | cos>=0 | cos<0 |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for log in logs:
        for step in steps:
            rows = log.krows.get(step, [])
            if not rows:
                continue
            for k in ks:
                layers, ratio, corr, cos, good, pos, neg = _summarize_k(rows, k)
                if layers == 0:
                    continue
                print(
                    f"| {log.name} | {step} | {k} | {layers} | {_fmt_sci(ratio)} | "
                    f"{_fmt_sci(corr)} | {_fmt(cos, 3)} | {good} | {pos} | {neg} |"
                )
    print()


def _print_apply(logs: list[LogData], steps: list[int]) -> None:
    print("## Applied Correction Scale")
    print()
    print("| log | step | logged updates | base med | raw frac med | eff frac med | eff frac p90 | scale med |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for log in logs:
        for step in steps:
            apply = log.apply.get(step)
            if apply is None:
                continue
            print(
                f"| {log.name} | {step} | {apply.count} | {_fmt(apply.base_med, 4)} | "
                f"{_fmt(apply.raw_frac_med, 4)} | {_fmt(apply.eff_frac_med, 4)} | "
                f"{_fmt(apply.eff_frac_p90, 4)} | {_fmt(apply.scale_med, 3)} |"
            )
    print()


def _print_read(logs: list[LogData], steps: list[int], ks: list[int], target_step: int, target_loss: float) -> None:
    print("## Mechanism Read")
    print()
    for log in logs:
        parsed_ks = sorted({row.k for rows in log.krows.values() for row in rows})
        if not parsed_ks:
            print(f"- `{log.name}`: no kdiag rows parsed.")
            continue
        requested_ks = [k for k in parsed_ks if k in ks]
        k = max(requested_ks or parsed_ks)
        good_steps = []
        dead_steps = []
        for step in steps:
            rows = log.krows.get(step, [])
            if not rows:
                continue
            layers, ratio, _corr, cos, good, _pos, _neg = _summarize_k(rows, k)
            apply = log.apply.get(step)
            if ratio is None or cos is None:
                continue
            local_ok = ratio < 1.0 and good >= math.ceil(0.9 * layers)
            scale_ok = apply is None or (apply.eff_frac_med is not None and apply.eff_frac_med >= 0.005)
            if local_ok and scale_ok:
                good_steps.append(step)
            else:
                dead_steps.append(step)
        print(
            f"- `{log.name}`: local K{k} correction is locally sane at "
            f"{good_steps if good_steps else 'no parsed steps'}; weak/bad at {dead_steps if dead_steps else 'none'}."
        )

    print()
    print(
        "Synthesis rule: if local loss improves and an applied correction exists but "
        "validation slope is still cold, the missing ingredient is not more local "
        "iterations. It is trajectory/schedule/state compatibility."
    )


def print_report(
    logs: list[LogData],
    *,
    steps: list[int],
    ks: list[int],
    target_step: int,
    target_loss: float,
) -> None:
    print("# Track 3 LocoProp-M Mechanism Report")
    print()
    _print_validation(logs, steps, target_step, target_loss)
    _print_k(logs, steps, ks)
    _print_apply(logs, steps)
    _print_read(logs, steps, ks, target_step, target_loss)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--steps", default="")
    parser.add_argument("--ks", default="5,10")
    parser.add_argument("--target-step", type=int, default=3000)
    parser.add_argument("--target-loss", type=float, default=3.28)
    args = parser.parse_args()

    logs = [parse_log(path) for path in _collect_paths(args.logs)]
    steps = _steps_from(args.steps, logs)
    ks = [int(item) for item in args.ks.split(",") if item.strip()]
    print_report(logs, steps=steps, ks=ks, target_step=args.target_step, target_loss=args.target_loss)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
