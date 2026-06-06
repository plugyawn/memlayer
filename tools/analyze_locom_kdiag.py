#!/usr/bin/env python3
"""Summarize LocoProp-M K-ladder diagnostics from training logs."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import median


LINE_RE = re.compile(r"locoprop_m_kdiag step=(?P<step>\d+)\s+l(?P<layer>\d+)\s+(?P<body>.*)")
ITEM_RE = re.compile(r"k(?P<k>\d+):(?P<body>[^|]+)")
KV_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([+-]?(?:inf|nan|[0-9.eE+-]+))", re.IGNORECASE)


def _finite(values: list[float]) -> list[float]:
    return [v for v in values if math.isfinite(v)]


def _median(values: list[float]) -> float | None:
    values = _finite(values)
    if not values:
        return None
    return float(median(values))


def _fmt(value: float | None) -> str:
    if value is None:
        return "nan"
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return f"{value:.3e}"


def _profile_name(path: str) -> str:
    stem = Path(path).stem
    return stem.removeprefix("track3_kdiag_")


def _default_inner_lr(profile: str) -> float | None:
    """Best-effort defaults for known run profiles.

    The training logs do not always include the inner local-optimizer LR, but
    our profile names do. This keeps recommendations reproducible from pulled
    logs without depending on chat context.
    """
    if "post-true-k10-lr1e3" in profile:
        return 1e-3
    if "post-true-k10-lr3e4" in profile:
        return 3e-4
    if "post-true-k10-lr2e4" in profile:
        return 2e-4
    if "post-true-k10-lr1e4" in profile:
        return 1e-4
    if "post-true-k10-alpha0" in profile:
        return 1e-5
    if "post-approx-k10-fixedtime-active" in profile or "pre-k10-fixedtime-active" in profile:
        return 4e-2
    if "post-approx" in profile or profile.startswith("pre-"):
        return 1e-1
    return None


def _parse_profile_inner_lrs(values: list[str]) -> dict[str, float]:
    mapping: dict[str, float] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"--profile-inner-lr must be PROFILE=LR, got {value!r}")
        profile, lr = value.split("=", 1)
        mapping[profile.strip()] = float(lr)
    return mapping


def parse_log(path: Path) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
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
        grouped[(str(row["path"]), int(row["step"]), int(row["k"]))].append(row)

    summary = []
    for (path, step, k), items in sorted(grouped.items()):
        ratios = [float(item.get("ratio", float("nan"))) for item in items]
        losses = [float(item.get("loss", float("nan"))) for item in items]
        norms = [float(item.get("corr_norm", float("nan"))) for item in items]
        cosines = [float(item.get("cos", float("nan"))) for item in items]
        raw_cosines = [float(item.get("raw_cos", float("nan"))) for item in items]
        summary.append(
            {
                "path": str(items[0]["path"]),
                "profile": _profile_name(path),
                "step": step,
                "k": k,
                "layers": len(items),
                "median_ratio": _median(ratios),
                "median_loss": _median(losses),
                "median_corr_norm": _median(norms),
                "median_cos": _median(cosines),
                "median_raw_cos": _median(raw_cosines),
                "bad_ratio_gt_1": sum(1 for value in ratios if math.isfinite(value) and value > 1.0),
                "nonfinite_ratio": sum(1 for value in ratios if not math.isfinite(value)),
                "nonfinite_corr": sum(1 for value in norms if not math.isfinite(value)),
                "bad_cos_lt_0": sum(1 for value in cosines if math.isfinite(value) and value < 0.0),
            }
        )
    return summary


def print_markdown(summary: list[dict[str, object]]) -> None:
    if not summary:
        print("No locoprop_m_kdiag rows found.")
        return
    print("| profile | step | k | layers | med loss/loss0 | med corr_norm | med cos | bad loss | nonfinite | bad cos |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in summary:
        ratio = row["median_ratio"]
        corr = row["median_corr_norm"]
        cos = row["median_cos"]
        print(
            f"| {row['profile']} | {row['step']} | {row['k']} | {row['layers']} | "
            f"{_fmt(ratio)} | {_fmt(corr)} | {cos:.3f} | "
            f"{row['bad_ratio_gt_1']} | "
            f"{int(row['nonfinite_ratio']) + int(row['nonfinite_corr'])} | "
            f"{row['bad_cos_lt_0']} |"
        )


def print_details(rows: list[dict[str, float | int | str]], detail_k: int | None, base_step_norm: float, norm_cap: float) -> None:
    if not rows:
        print("No locoprop_m_kdiag rows found.")
        return
    grouped: dict[str, list[dict[str, float | int | str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["path"])].append(row)

    max_norm = base_step_norm * norm_cap
    print("| profile | step | k | layer | loss/loss0 | corr_norm | cos | cap_scale |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for path, items in sorted(grouped.items()):
        if detail_k is None:
            k_values = [int(item["k"]) for item in items]
            selected_k = max(k_values)
        else:
            selected_k = detail_k
        for item in sorted(
            (item for item in items if int(item["k"]) == selected_k),
            key=lambda row: (int(row["step"]), int(row["layer"])),
        ):
            corr = float(item.get("corr_norm", float("nan")))
            ratio = float(item.get("ratio", float("nan")))
            cos = float(item.get("cos", float("nan")))
            cap_scale = max_norm / corr if math.isfinite(corr) and corr > 0 else float("nan")
            print(
                f"| {_profile_name(path)} | {int(item['step'])} | {selected_k} | {int(item['layer'])} | "
                f"{_fmt(ratio)} | {_fmt(corr)} | {cos:.3f} | {_fmt(cap_scale)} |"
            )


def print_gate_report(
    summary: list[dict[str, object]],
    *,
    corr_min: float,
    corr_max: float,
    max_bad_loss: int,
    max_nonfinite: int,
) -> None:
    if not summary:
        print("No locoprop_m_kdiag rows found.")
        return
    print("| profile | step | k | med loss/loss0 | med corr_norm | bad loss | nonfinite | pass local gate |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in summary:
        ratio = row["median_ratio"]
        corr = row["median_corr_norm"]
        nonfinite = int(row["nonfinite_ratio"]) + int(row["nonfinite_corr"])
        passes = (
            ratio is not None
            and corr is not None
            and math.isfinite(ratio)
            and math.isfinite(corr)
            and ratio < 1.0
            and corr_min <= corr <= corr_max
            and int(row["bad_ratio_gt_1"]) <= max_bad_loss
            and nonfinite <= max_nonfinite
        )
        print(
            f"| {row['profile']} | {row['step']} | {row['k']} | "
            f"{_fmt(ratio)} | {_fmt(corr)} | {row['bad_ratio_gt_1']} | "
            f"{nonfinite} | {'yes' if passes else 'no'} |"
        )


def _max_k_summary_rows(summary: list[dict[str, object]]) -> list[dict[str, object]]:
    by_profile: dict[tuple[str, int], dict[str, object]] = {}
    for row in summary:
        key = (str(row["profile"]), int(row["step"]))
        prior = by_profile.get(key)
        if prior is None or int(row["k"]) > int(prior["k"]):
            by_profile[key] = row
    return sorted(by_profile.values(), key=lambda row: (str(row["profile"]), int(row["step"])))


def _rows_by_profile_step_k(rows: list[dict[str, float | int | str]]) -> dict[tuple[str, int, int], list[dict[str, float | int | str]]]:
    grouped: dict[tuple[str, int, int], list[dict[str, float | int | str]]] = defaultdict(list)
    for row in rows:
        grouped[(_profile_name(str(row["path"])), int(row["step"]), int(row["k"]))].append(row)
    return grouped


def _recommendation(
    row: dict[str, object],
    *,
    corr_min: float,
    corr_max: float,
    max_bad_loss: int,
    max_nonfinite: int,
) -> str:
    ratio = row["median_ratio"]
    corr = row["median_corr_norm"]
    nonfinite = int(row["nonfinite_ratio"]) + int(row["nonfinite_corr"])
    bad_loss = int(row["bad_ratio_gt_1"])
    if nonfinite > max_nonfinite:
        return "dead: nonfinite correction"
    if ratio is None or corr is None or not math.isfinite(float(ratio)) or not math.isfinite(float(corr)):
        return "dead: invalid median"
    ratio_f = float(ratio)
    corr_f = float(corr)
    if bad_loss > max_bad_loss and ratio_f > 1.0:
        return "dead: local loss worsens"
    if ratio_f < 1.0 and bad_loss <= max_bad_loss and corr_f < corr_min:
        return "scale up true local step"
    if ratio_f < 1.0 and bad_loss <= max_bad_loss and corr_min <= corr_f <= corr_max:
        return "promote active screen"
    if ratio_f < 1.0 and bad_loss <= max_bad_loss and corr_f > corr_max:
        return "too large: reduce lr/cap"
    if ratio_f < 1.0:
        return "layer-restrict or gate harder"
    return "do not promote"


def print_recommendations(
    rows: list[dict[str, float | int | str]],
    summary: list[dict[str, object]],
    *,
    base_step_norm: float,
    norm_cap: float,
    corr_min: float,
    corr_max: float,
    max_bad_loss: int,
    max_nonfinite: int,
    profile_inner_lrs: dict[str, float],
) -> None:
    if not summary:
        print("No locoprop_m_kdiag rows found.")
        return

    grouped = _rows_by_profile_step_k(rows)
    max_norm = base_step_norm * norm_cap
    print("| profile | step | k | med loss/loss0 | med corr_norm | bad loss | nonfinite | pos-cos layers | stable layers | median cap multiplier | inner_lr | lr@corr_min | lr@corr_max | lr@median_cap | recommendation |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in _max_k_summary_rows(summary):
        profile = str(row["profile"])
        step = int(row["step"])
        k = int(row["k"])
        layer_rows = grouped.get((profile, step, k), [])
        pos_cos_layers = sum(
            1 for item in layer_rows
            if math.isfinite(float(item.get("cos", float("nan")))) and float(item.get("cos", 0.0)) >= 0.0
        )
        stable_layers = sum(
            1 for item in layer_rows
            if math.isfinite(float(item.get("ratio", float("nan"))))
            and math.isfinite(float(item.get("corr_norm", float("nan"))))
            and float(item.get("ratio", float("inf"))) < 1.0
        )
        cap_multipliers = [
            max_norm / float(item["corr_norm"])
            for item in layer_rows
            if math.isfinite(float(item.get("corr_norm", float("nan")))) and float(item["corr_norm"]) > 0
        ]
        cap_multiplier = _median(cap_multipliers)
        inner_lr = profile_inner_lrs.get(profile, _default_inner_lr(profile))
        median_corr = row["median_corr_norm"]
        if (
            inner_lr is not None
            and median_corr is not None
            and math.isfinite(float(median_corr))
            and float(median_corr) > 0.0
        ):
            corr_f = float(median_corr)
            lr_corr_min = inner_lr * corr_min / corr_f
            lr_corr_max = inner_lr * corr_max / corr_f
        else:
            lr_corr_min = None
            lr_corr_max = None
        lr_cap = (
            inner_lr * cap_multiplier
            if inner_lr is not None and cap_multiplier is not None and math.isfinite(float(cap_multiplier))
            else None
        )
        nonfinite = int(row["nonfinite_ratio"]) + int(row["nonfinite_corr"])
        print(
            f"| {profile} | {step} | {k} | {_fmt(row['median_ratio'])} | "
            f"{_fmt(row['median_corr_norm'])} | {row['bad_ratio_gt_1']} | {nonfinite} | "
            f"{pos_cos_layers}/{len(layer_rows)} | {stable_layers}/{len(layer_rows)} | "
            f"{_fmt(cap_multiplier)} | {_fmt(inner_lr)} | {_fmt(lr_corr_min)} | "
            f"{_fmt(lr_corr_max)} | {_fmt(lr_cap)} | "
            f"{_recommendation(row, corr_min=corr_min, corr_max=corr_max, max_bad_loss=max_bad_loss, max_nonfinite=max_nonfinite)} |"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--details", action="store_true", help="Print per-layer rows for one K per profile")
    parser.add_argument("--detail-k", type=int, default=None, help="K to show in --details; default: max K per profile")
    parser.add_argument("--gate-report", action="store_true", help="Print local promotion gates")
    parser.add_argument("--recommend", action="store_true", help="Print one-row decision per profile at max K")
    parser.add_argument("--base-step-norm", type=float, default=4.263e-2)
    parser.add_argument("--norm-cap", type=float, default=0.20)
    parser.add_argument("--corr-min", type=float, default=1e-3)
    parser.add_argument("--corr-max", type=float, default=1e-2)
    parser.add_argument("--max-bad-loss", type=int, default=2)
    parser.add_argument("--max-nonfinite", type=int, default=0)
    parser.add_argument(
        "--profile-inner-lr",
        action="append",
        default=[],
        metavar="PROFILE=LR",
        help="Override inferred inner LR for --recommend. May be repeated.",
    )
    args = parser.parse_args()

    rows: list[dict[str, float | int | str]] = []
    for path in args.logs:
        rows.extend(parse_log(path))
    summary = summarize(rows)
    if args.json:
        print(json.dumps({"rows": rows, "summary": summary}, indent=2, sort_keys=True))
    elif args.details:
        print_details(rows, args.detail_k, args.base_step_norm, args.norm_cap)
    elif args.gate_report:
        print_gate_report(
            summary,
            corr_min=args.corr_min,
            corr_max=args.corr_max,
            max_bad_loss=args.max_bad_loss,
            max_nonfinite=args.max_nonfinite,
        )
    elif args.recommend:
        print_recommendations(
            rows,
            summary,
            base_step_norm=args.base_step_norm,
            norm_cap=args.norm_cap,
            corr_min=args.corr_min,
            corr_max=args.corr_max,
            max_bad_loss=args.max_bad_loss,
            max_nonfinite=args.max_nonfinite,
            profile_inner_lrs=_parse_profile_inner_lrs(args.profile_inner_lr),
        )
    else:
        print_markdown(summary)


if __name__ == "__main__":
    main()
