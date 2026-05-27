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
    r"(?: step_ms:(?P<step_ms>[0-9.]+) refresh:(?P<refresh>[01]))?"
)
PEAK_RE = re.compile(r"peak memory allocated: (?P<alloc>\d+) MiB reserved: (?P<reserved>\d+) MiB")


def empty_case(name: str) -> dict:
    return {
        "case": name,
        "log": None,
        "returncode": None,
        "final_step": None,
        "total_steps": None,
        "final_val_loss": None,
        "final_train_time_s": None,
        "final_step_avg_ms": None,
        "peak_alloc_mib": None,
        "peak_reserved_mib": None,
        "refresh_step_ms_avg": None,
        "nonrefresh_step_ms_avg": None,
    }


def finish_step_ms(case: dict, refresh_values: list[float], nonrefresh_values: list[float]) -> None:
    if refresh_values:
        case["refresh_step_ms_avg"] = round(sum(refresh_values) / len(refresh_values), 3)
    if nonrefresh_values:
        case["nonrefresh_step_ms_avg"] = round(sum(nonrefresh_values) / len(nonrefresh_values), 3)


def parse_log(path: Path) -> list[dict]:
    cases: list[dict] = []
    current = empty_case(path.stem)
    current["log"] = str(path)
    refresh_values: list[float] = []
    nonrefresh_values: list[float] = []
    saw_markers = False
    active = True

    def flush() -> None:
        nonlocal current, refresh_values, nonrefresh_values
        finish_step_ms(current, refresh_values, nonrefresh_values)
        if current["final_step"] is not None or current["returncode"] is not None:
            cases.append(current)
        current = empty_case(path.stem)
        current["log"] = str(path)
        refresh_values = []
        nonrefresh_values = []

    for line in path.read_text(errors="replace").splitlines():
        if m := CASE_START_RE.match(line):
            if saw_markers:
                flush()
            saw_markers = True
            active = True
            current = empty_case(m.group(1))
            current["log"] = str(path)
            refresh_values = []
            nonrefresh_values = []
            continue
        if m := CASE_END_RE.match(line):
            current["returncode"] = 0
            active = False
            continue
        if saw_markers and not active:
            continue
        if m := STEP_RE.search(line):
            current["final_step"] = int(m.group("step"))
            current["total_steps"] = int(m.group("total"))
            if m.group("val_loss") is not None:
                current["final_val_loss"] = float(m.group("val_loss"))
            current["final_train_time_s"] = round(int(m.group("train_ms")) / 1000.0, 3)
            current["final_step_avg_ms"] = float(m.group("step_avg"))
            if m.group("step_ms") is not None:
                target = refresh_values if m.group("refresh") == "1" else nonrefresh_values
                target.append(float(m.group("step_ms")))
            continue
        if m := PEAK_RE.search(line):
            current["peak_alloc_mib"] = int(m.group("alloc"))
            current["peak_reserved_mib"] = int(m.group("reserved"))

    flush()
    return cases


def md_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}" if value < 100 else f"{value:.2f}"
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = []
    for path in args.logs:
        rows.extend(parse_log(path))

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return

    columns = [
        "case",
        "final_step",
        "final_val_loss",
        "final_train_time_s",
        "final_step_avg_ms",
        "refresh_step_ms_avg",
        "nonrefresh_step_ms_avg",
        "peak_alloc_mib",
    ]
    print("| " + " | ".join(columns) + " |")
    print("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        print("| " + " | ".join(md_value(row.get(col)) for col in columns) + " |")


if __name__ == "__main__":
    main()
