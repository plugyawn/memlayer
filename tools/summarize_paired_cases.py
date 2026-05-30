#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


CASE_START_RE = re.compile(r"^===== NEWTONV_CASE_START\s+(\S+)")
CASE_END_RE = re.compile(r"^===== NEWTONV_CASE_END\s+(\S+)")
STEP_RE = re.compile(
    r"step:(?P<step>\d+)/(?P<total>\d+)"
    r"(?: val_loss:(?P<val_loss>[0-9.]+))?"
    r" train_time:(?P<train_ms>\d+)ms step_avg:(?P<step_avg>[0-9.]+)ms"
)


def parse_logs(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        group = path.stem
        current_case = None
        current = {}

        def flush():
            nonlocal current_case, current
            if current_case and current.get("final_step") is not None:
                rows.append({"log": str(path), "group": group, "case": current_case, **current})
            current_case = None
            current = {}

        for line in path.read_text(errors="replace").splitlines():
            if line.lstrip().startswith('"tail":'):
                continue
            if m := CASE_START_RE.match(line):
                name = m.group(1)
                if name.startswith("paired_"):
                    flush()
                    current_case = name
                    current = {}
                else:
                    flush()
                    group = name
                continue
            if m := CASE_END_RE.match(line):
                if current_case == m.group(1):
                    flush()
                continue
            if current_case and (m := STEP_RE.search(line)):
                current["final_step"] = int(m.group("step"))
                current["total_steps"] = int(m.group("total"))
                if m.group("val_loss") is not None:
                    current["val_loss"] = float(m.group("val_loss"))
                current["train_time_s"] = round(int(m.group("train_ms")) / 1000.0, 3)
                current["step_avg_ms"] = float(m.group("step_avg"))
        flush()
    return rows


def summarize(rows: list[dict]) -> list[dict]:
    grouped = {}
    for row in rows:
        grouped.setdefault((row["log"], row["group"]), {})[row["case"]] = row

    summaries = []
    for (log, group), cases in grouped.items():
        active = cases.get("paired_active")
        noop = cases.get("paired_noop")
        noop2 = cases.get("paired_noop2")
        noop_losses = [
            row["val_loss"]
            for row in (noop, noop2)
            if row is not None and row.get("val_loss") is not None
        ]
        active_loss = active.get("val_loss") if active else None
        noop_mean = sum(noop_losses) / len(noop_losses) if noop_losses else None
        delta = active_loss - noop_mean if active_loss is not None and noop_mean is not None else None
        beats_both = (
            bool(noop_losses)
            and active_loss is not None
            and len(noop_losses) == 2
            and all(active_loss < loss for loss in noop_losses)
        )
        summaries.append(
            {
                "log": log,
                "group": group,
                "active_step": active.get("final_step") if active else None,
                "active": active_loss,
                "noop": noop.get("val_loss") if noop else None,
                "noop2": noop2.get("val_loss") if noop2 else None,
                "noop_mean": noop_mean,
                "delta_vs_noop_mean": delta,
                "beats_both": beats_both if len(noop_losses) == 2 and active_loss is not None else None,
                "active_step_avg_ms": active.get("step_avg_ms") if active else None,
            }
        )
    return summaries


def md(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:+.4f}" if abs(value) < 1 else f"{value:.4f}"
    return str(value)


def summarize_name(group: str) -> dict[str, str]:
    fields = {}
    if "_parallel_" in group:
        fields["component"] = "parallel"
    elif "_orthogonal_" in group:
        fields["component"] = "orthogonal"
    elif "_full_" in group:
        fields["component"] = "full"
    if m := re.search(r"_blend(?P<blend>[0-9]+)$", group):
        fields["blend"] = "0." + m.group("blend")[1:] if m.group("blend").startswith("0") else m.group("blend")
    if m := re.search(r"_b(?P<blend>[0-9]+p[0-9]+)", group):
        fields["blend"] = m.group("blend").replace("p", ".")
    return fields


def print_table(rows: list[dict]) -> None:
    columns = [
        "group",
        "component",
        "blend",
        "active_step",
        "active",
        "noop",
        "noop2",
        "noop_mean",
        "delta_vs_noop_mean",
        "beats_both",
        "active_step_avg_ms",
    ]
    print("| " + " | ".join(columns) + " |")
    print("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        row = {**summarize_name(row["group"]), **row}
        print("| " + " | ".join(md(row.get(col)) for col in columns) + " |")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    summaries = summarize(parse_logs(args.logs))
    if args.json:
        print(json.dumps(summaries, indent=2, sort_keys=True))
    else:
        print_table(summaries)


if __name__ == "__main__":
    main()
