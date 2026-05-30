#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parse_loco_full_diagnostics import parse as parse_diagnostics
from summarize_paired_cases import parse_logs, summarize


RAW_NAME_BY_SURFACE = {
    "v": "full_v_add_rawscale",
    "o": "full_o_add_rawscale",
    "mlp_fc": "full_mlp_fc_add_rawscale",
}


def infer_surface(group: str) -> str:
    if "_mlp_fc" in group or group.endswith("mlp_fc"):
        return "mlp_fc"
    if re.search(r"(^|_)v($|_)", group):
        return "v"
    if re.search(r"(^|_)o($|_)", group):
        return "o"
    return ""


def md(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:+.4f}" if abs(value) < 1 else f"{value:.4f}"
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--min-delta", type=float, default=0.003)
    parser.add_argument("--max-step40-regression", type=float, default=0.02)
    parser.add_argument("--max-overhead-pct", type=float, default=1.0)
    args = parser.parse_args()

    case_rows = parse_logs(args.logs)
    cases_by_group = {}
    for row in case_rows:
        cases_by_group.setdefault((row["log"], row["group"]), {})[row["case"]] = row

    raw_by_surface = {}
    for path in args.logs:
        for row in parse_diagnostics(path)["precond"]:
            if row.get("case") != "paired_active":
                continue
            for surface, name in RAW_NAME_BY_SURFACE.items():
                if row.get("name") != name:
                    continue
                prev = raw_by_surface.get(surface)
                if prev is None or (row.get("step") or -1) > (prev.get("step") or -1):
                    raw_by_surface[surface] = row

    rows = []
    for summary in summarize(case_rows):
        surface = infer_surface(summary["group"])
        cases = cases_by_group.get((summary["log"], summary["group"]), {})
        noop_times = [
            row.get("step_avg_ms")
            for row in (cases.get("paired_noop"), cases.get("paired_noop2"))
            if row is not None and row.get("step_avg_ms") is not None
        ]
        noop_time_mean = sum(noop_times) / len(noop_times) if noop_times else None
        active_time = summary.get("active_step_avg_ms")
        overhead_pct = (
            (active_time - noop_time_mean) / noop_time_mean * 100.0
            if active_time is not None and noop_time_mean
            else None
        )
        delta = summary.get("delta_vs_noop_mean")
        delta40 = summary.get("delta_40")
        improves_mean = delta is not None and delta <= -args.min_delta
        no_bad_step40 = delta40 is not None and delta40 <= args.max_step40_regression
        overhead_ok = overhead_pct is not None and overhead_pct <= args.max_overhead_pct
        passed = bool(summary.get("beats_both")) and improves_mean and no_bad_step40 and overhead_ok
        raw = raw_by_surface.get(surface, {})
        rows.append(
            {
                "surface": surface,
                "group": summary["group"],
                "active_40": summary.get("active_40"),
                "delta_40": delta40,
                "active": summary.get("active"),
                "noop": summary.get("noop"),
                "noop2": summary.get("noop2"),
                "noop_mean": summary.get("noop_mean"),
                "delta": delta,
                "beats_both": summary.get("beats_both"),
                "overhead_pct": overhead_pct,
                "raw_step": raw.get("step"),
                "raw_ref_norm": raw.get("ref_norm_mean"),
                "raw_ref_delta": raw.get("ref_delta_mean"),
                "raw_ref_cos": raw.get("ref_cos_mean"),
                "gate_pass": passed,
            }
        )

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return

    columns = [
        "surface",
        "active_40",
        "delta_40",
        "active",
        "noop",
        "noop2",
        "noop_mean",
        "delta",
        "beats_both",
        "overhead_pct",
        "raw_step",
        "raw_ref_norm",
        "raw_ref_delta",
        "raw_ref_cos",
        "gate_pass",
    ]
    print("| " + " | ".join(columns) + " |")
    print("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        print("| " + " | ".join(md(row.get(col)) for col in columns) + " |")


if __name__ == "__main__":
    main()
