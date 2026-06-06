#!/usr/bin/env python3
"""Summarize whether extra LocoProp-M local steps are doing useful work.

This is intentionally separate from analyze_locom_kdiag.py. The kdiag analyzer
answers "is a given K locally sane?" This script answers "where is the knee?"
by comparing K values inside each profile and step.
"""

from __future__ import annotations

import argparse
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import median


LINE_RE = re.compile(r"locoprop_m_kdiag step=(?P<step>\d+)\s+l(?P<layer>\d+)\s+(?P<body>.*)")
ITEM_RE = re.compile(r"k(?P<k>\d+):(?P<body>[^|]+)")
KV_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([+-]?(?:inf|nan|[0-9.eE+-]+))", re.IGNORECASE)


def _profile_name(path: Path) -> str:
    return path.stem.removeprefix("track3_kdiag_")


def _finite(values: list[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def _median(values: list[float]) -> float | None:
    values = _finite(values)
    return None if not values else float(median(values))


def _fmt(value: float | None) -> str:
    if value is None:
        return "nan"
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return f"{value:.3e}"


def _fmt_ratio(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{100.0 * value:.1f}%"


def parse_log(path: Path) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    profile = _profile_name(path)
    for line in path.read_text(errors="replace").splitlines():
        match = LINE_RE.search(line)
        if not match:
            continue
        step = int(match["step"])
        layer = int(match["layer"])
        for item in ITEM_RE.finditer(match["body"]):
            values = {key: float(value) for key, value in KV_RE.findall(item["body"])}
            rows.append(
                {
                    "path": str(path),
                    "profile": profile,
                    "step": step,
                    "layer": layer,
                    "k": int(item["k"]),
                    **values,
                }
            )
    return rows


def summarize(rows: list[dict[str, float | int | str]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, int, int], list[dict[str, float | int | str]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["profile"]), int(row["step"]), int(row["k"]))].append(row)

    out: list[dict[str, object]] = []
    for (profile, step, k), items in sorted(grouped.items()):
        ratios = [float(item.get("ratio", float("nan"))) for item in items]
        corr_norms = [float(item.get("corr_norm", float("nan"))) for item in items]
        cosines = [float(item.get("cos", float("nan"))) for item in items]
        median_ratio = _median(ratios)
        out.append(
            {
                "profile": profile,
                "step": step,
                "k": k,
                "layers": len(items),
                "median_ratio": median_ratio,
                "median_gain": (
                    None
                    if median_ratio is None or not math.isfinite(float(median_ratio))
                    else 1.0 - float(median_ratio)
                ),
                "median_corr_norm": _median(corr_norms),
                "median_cos": _median(cosines),
                "bad_loss": sum(1 for value in ratios if math.isfinite(value) and value > 1.0),
                "nonfinite": sum(1 for value in ratios + corr_norms if not math.isfinite(value)),
                "bad_cos": sum(1 for value in cosines if math.isfinite(value) and value < 0.0),
            }
        )
    return out


def _by_profile_step(summary: list[dict[str, object]]) -> dict[tuple[str, int], dict[int, dict[str, object]]]:
    grouped: dict[tuple[str, int], dict[int, dict[str, object]]] = defaultdict(dict)
    for row in summary:
        grouped[(str(row["profile"]), int(row["step"]))][int(row["k"])] = row
    return grouped


def _smallest_k_at_gain(rows_by_k: dict[int, dict[str, object]], ref_k: int, threshold: float) -> int | None:
    ref = rows_by_k.get(ref_k)
    if not ref:
        return None
    ref_gain = ref.get("median_gain")
    if ref_gain is None or not math.isfinite(float(ref_gain)) or float(ref_gain) <= 0:
        return None
    for k in sorted(rows_by_k):
        row = rows_by_k[k]
        gain = row.get("median_gain")
        if gain is None or not math.isfinite(float(gain)):
            continue
        if float(gain) / float(ref_gain) >= threshold:
            return k
    return None


def print_markdown(summary: list[dict[str, object]], ref_k: int, gain_threshold: float) -> None:
    grouped = _by_profile_step(summary)
    print("| profile | step | k | med loss/loss0 | med gain | gain/ref | corr/ref | med cos | bad loss | bad cos | nonfinite |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for (profile, step), rows_by_k in sorted(grouped.items()):
        ref = rows_by_k.get(ref_k)
        ref_gain = ref.get("median_gain") if ref else None
        ref_corr = ref.get("median_corr_norm") if ref else None
        for k in sorted(rows_by_k):
            row = rows_by_k[k]
            gain = row.get("median_gain")
            corr = row.get("median_corr_norm")
            gain_ref = (
                None
                if ref_gain is None or gain is None or not math.isfinite(float(ref_gain)) or float(ref_gain) <= 0
                else float(gain) / float(ref_gain)
            )
            corr_ref = (
                None
                if ref_corr is None or corr is None or not math.isfinite(float(ref_corr)) or float(ref_corr) <= 0
                else float(corr) / float(ref_corr)
            )
            print(
                f"| {profile} | {step} | {k} | {_fmt(row.get('median_ratio'))} | "
                f"{_fmt(gain)} | {_fmt_ratio(gain_ref)} | {_fmt_ratio(corr_ref)} | "
                f"{float(row.get('median_cos') or float('nan')):.3f} | "
                f"{row['bad_loss']} | {row['bad_cos']} | {row['nonfinite']} |"
            )

    print()
    print("| profile | step | ref_k | gain threshold | smallest K | read |")
    print("| --- | ---: | ---: | ---: | ---: | --- |")
    for (profile, step), rows_by_k in sorted(grouped.items()):
        knee = _smallest_k_at_gain(rows_by_k, ref_k, gain_threshold)
        if knee is None:
            read = "no stable positive-gain knee"
        elif knee >= ref_k:
            read = "ref K still needed by this threshold"
        elif knee >= 8:
            read = "K8-like knee; test K8 active before K10"
        elif knee >= 5:
            read = "K5-like knee; test cheaper K5 active"
        else:
            read = "very early knee; correction scale may matter more than K"
        print(f"| {profile} | {step} | {ref_k} | {_fmt_ratio(gain_threshold)} | {knee if knee is not None else 'nan'} | {read} |")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--ref-k", type=int, default=10)
    parser.add_argument("--gain-threshold", type=float, default=0.80)
    args = parser.parse_args()

    rows: list[dict[str, float | int | str]] = []
    for path in args.logs:
        rows.extend(parse_log(path))
    print_markdown(summarize(rows), args.ref_k, args.gain_threshold)


if __name__ == "__main__":
    main()
