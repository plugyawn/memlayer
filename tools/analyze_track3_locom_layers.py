#!/usr/bin/env python3
"""Summarize per-layer LocoProp-M local health from kdiag rows.

The global mechanism reports tell us that K=5 is externally enough and that the
post-1800 suffix does not improve validation.  This script answers the narrower
question: are all c_fc layers similarly healthy, or is the prefix signal carried
by a subset of layers?

The `locoprop_m_apply` rows currently do not contain layer ids, so this report
uses the local diagnostic gate approximation:

    accepted ~= loss_ratio < 1 and cos >= min_cos

That matches the current `require_loss_decrease=1, min_cos_desc=0.0` setting.
"""

from __future__ import annotations

import argparse
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median


KDIAG_RE = re.compile(r"locoprop_m_kdiag step=(?P<step>\d+)\s+l(?P<layer>\d+)\s+(?P<body>.*)")
ITEM_RE = re.compile(r"k(?P<k>\d+):(?P<body>[^|]+)")
KV_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([+-]?(?:inf|nan|[0-9.eE+-]+))", re.IGNORECASE)


@dataclass(frozen=True)
class KDiag:
    step: int
    layer: int
    k: int
    ratio: float
    corr_norm: float
    cos: float


@dataclass
class LayerSummary:
    layer: int
    count: int
    med_ratio: float | None
    med_gain: float | None
    med_corr_norm: float | None
    med_cos: float | None
    good_loss_frac: float
    accepted_frac: float
    strong_frac: float
    neg_cos_frac: float
    unstable_frac: float
    label: str


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


def _frac(count: int, total: int) -> float:
    return float(count / total) if total else float("nan")


def _fmt(value: float | None, digits: int = 3) -> str:
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


def _steps_from(text: str, rows: list[KDiag]) -> set[int] | None:
    if text:
        return {int(item) for item in text.split(",") if item.strip()}
    return None


def parse_log(path: Path) -> list[KDiag]:
    rows: list[KDiag] = []
    for line in path.read_text(errors="replace").splitlines():
        match = KDIAG_RE.search(line)
        if not match:
            continue
        step = int(match["step"])
        layer = int(match["layer"])
        for item in ITEM_RE.finditer(match["body"]):
            values = {key: _float(value) for key, value in KV_RE.findall(item["body"])}
            rows.append(
                KDiag(
                    step=step,
                    layer=layer,
                    k=int(item["k"]),
                    ratio=values.get("ratio", float("nan")),
                    corr_norm=values.get("corr_norm", float("nan")),
                    cos=values.get("cos", float("nan")),
                )
            )
    return rows


def _label(
    *,
    count: int,
    med_gain: float | None,
    accepted_frac: float,
    strong_frac: float,
    neg_cos_frac: float,
    unstable_frac: float,
) -> str:
    if count == 0:
        return "missing"
    if unstable_frac >= 0.25:
        return "unstable"
    if neg_cos_frac >= 0.5:
        return "opposing"
    if strong_frac >= 0.5:
        return "strong"
    if accepted_frac >= 0.5 and med_gain is not None and med_gain > 0.0:
        return "accepted-weak"
    if accepted_frac >= 0.25:
        return "mixed"
    return "weak"


def summarize_layers(
    rows: list[KDiag],
    *,
    k: int,
    steps: set[int] | None,
    min_gain: float,
    min_cos: float,
    unstable_ratio: float,
) -> list[LayerSummary]:
    grouped: dict[int, list[KDiag]] = defaultdict(list)
    for row in rows:
        if row.k != k:
            continue
        if steps is not None and row.step not in steps:
            continue
        grouped[row.layer].append(row)

    summaries: list[LayerSummary] = []
    for layer in sorted(grouped):
        layer_rows = grouped[layer]
        total = len(layer_rows)
        ratios = [row.ratio for row in layer_rows]
        gains = [1.0 - row.ratio for row in layer_rows if math.isfinite(row.ratio)]
        corr_norms = [row.corr_norm for row in layer_rows]
        cosines = [row.cos for row in layer_rows]
        good = sum(1 for row in layer_rows if math.isfinite(row.ratio) and row.ratio < 1.0)
        accepted = sum(
            1
            for row in layer_rows
            if math.isfinite(row.ratio)
            and math.isfinite(row.cos)
            and row.ratio < 1.0
            and row.cos >= min_cos
        )
        strong = sum(
            1
            for row in layer_rows
            if math.isfinite(row.ratio)
            and math.isfinite(row.cos)
            and (1.0 - row.ratio) >= min_gain
            and row.cos >= min_cos
        )
        neg = sum(1 for row in layer_rows if math.isfinite(row.cos) and row.cos < min_cos)
        unstable = sum(1 for row in layer_rows if (not math.isfinite(row.ratio)) or row.ratio > unstable_ratio)
        med_gain = _median(gains)
        accepted_frac = _frac(accepted, total)
        strong_frac = _frac(strong, total)
        neg_cos_frac = _frac(neg, total)
        unstable_frac = _frac(unstable, total)
        summaries.append(
            LayerSummary(
                layer=layer,
                count=total,
                med_ratio=_median(ratios),
                med_gain=med_gain,
                med_corr_norm=_median(corr_norms),
                med_cos=_median(cosines),
                good_loss_frac=_frac(good, total),
                accepted_frac=accepted_frac,
                strong_frac=strong_frac,
                neg_cos_frac=neg_cos_frac,
                unstable_frac=unstable_frac,
                label=_label(
                    count=total,
                    med_gain=med_gain,
                    accepted_frac=accepted_frac,
                    strong_frac=strong_frac,
                    neg_cos_frac=neg_cos_frac,
                    unstable_frac=unstable_frac,
                ),
            )
        )
    return summaries


def _print_summary(path: Path, rows: list[KDiag], summaries: list[LayerSummary], *, k: int, steps: set[int] | None) -> None:
    print(f"## {_name(path)}")
    print()
    parsed_steps = sorted({row.step for row in rows if row.k == k})
    selected_steps = sorted(steps) if steps is not None else parsed_steps
    print(f"- file: `{path}`")
    print(f"- K: `{k}`")
    print(f"- selected steps: `{','.join(str(step) for step in selected_steps) if selected_steps else 'none'}`")
    print()
    print("| layer | samples | med loss/loss0 | med gain | med corr_norm | med cos | good loss | accepted | strong | neg cos | unstable | label |")
    print("| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for item in summaries:
        print(
            f"| {item.layer} | {item.count} | {_fmt_sci(item.med_ratio)} | {_fmt_sci(item.med_gain)} | "
            f"{_fmt_sci(item.med_corr_norm)} | {_fmt(item.med_cos, 3)} | "
            f"{_fmt(item.good_loss_frac, 2)} | {_fmt(item.accepted_frac, 2)} | "
            f"{_fmt(item.strong_frac, 2)} | {_fmt(item.neg_cos_frac, 2)} | "
            f"{_fmt(item.unstable_frac, 2)} | {item.label} |"
        )
    print()

    strong_layers = [item.layer for item in summaries if item.label == "strong"]
    accepted_layers = [item.layer for item in summaries if item.label in {"strong", "accepted-weak"}]
    risky_layers = [item.layer for item in summaries if item.label in {"opposing", "unstable"}]
    print("Read:")
    print(f"- strong layers: {strong_layers if strong_layers else 'none'}")
    print(f"- accepted weak/strong layers: {accepted_layers if accepted_layers else 'none'}")
    print(f"- risky layers: {risky_layers if risky_layers else 'none'}")
    if strong_layers:
        print(f"- next subset candidate: `WR_LOCOM_LAYER_SET={','.join(str(layer) for layer in strong_layers)}`")
    elif accepted_layers:
        print(f"- next subset candidate: `WR_LOCOM_LAYER_SET={','.join(str(layer) for layer in accepted_layers)}`")
    else:
        print("- next subset candidate: none from these diagnostics")
    print()


def print_report(
    logs: list[Path],
    *,
    k: int,
    steps_text: str,
    min_gain: float,
    min_cos: float,
    unstable_ratio: float,
) -> None:
    print("# Track 3 LocoProp-M Per-Layer Health")
    print()
    print(
        "Gate approximation: `accepted ~= loss/loss0 < 1 and cos >= min_cos`. "
        "The apply logs do not include layer ids, so use this as a layer-health screen, not an exact apply trace."
    )
    print()
    for path in logs:
        rows = parse_log(path)
        steps = _steps_from(steps_text, rows)
        summaries = summarize_layers(
            rows,
            k=k,
            steps=steps,
            min_gain=min_gain,
            min_cos=min_cos,
            unstable_ratio=unstable_ratio,
        )
        _print_summary(path, rows, summaries, k=k, steps=steps)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--steps", default="")
    parser.add_argument("--min-gain", type=float, default=0.08)
    parser.add_argument("--min-cos", type=float, default=0.0)
    parser.add_argument("--unstable-ratio", type=float, default=1.05)
    args = parser.parse_args()

    print_report(
        _collect_paths(args.logs),
        k=args.k,
        steps_text=args.steps,
        min_gain=args.min_gain,
        min_cos=args.min_cos,
        unstable_ratio=args.unstable_ratio,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
