#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


PRECOND_RE = re.compile(r"loco_full_precond step=(?P<step>\d+) (?P<body>.*)$")
PRECOND_SEG_RE = re.compile(
    r"(?P<name>\w+):n=(?P<n>\d+) layers=(?P<layers>[^ ]+) "
    r"blend=(?P<blend>[-+0-9.eE]+) "
    r"norm=(?P<norm_mean>[-+0-9.eE]+)/(?P<norm_min>[-+0-9.eE]+)/(?P<norm_max>[-+0-9.eE]+) "
    r"delta=(?P<delta_mean>[-+0-9.eE]+)/(?P<delta_min>[-+0-9.eE]+)/(?P<delta_max>[-+0-9.eE]+) "
    r"cos=(?P<cos_mean>[-+0-9.eE]+)/(?P<cos_min>[-+0-9.eE]+)/(?P<cos_max>[-+0-9.eE]+)"
    r"(?: target_delta=(?P<target_delta_mean>[-+0-9.eE]+)/(?P<target_delta_min>[-+0-9.eE]+)/(?P<target_delta_max>[-+0-9.eE]+) "
    r"target_cos=(?P<target_cos_mean>[-+0-9.eE]+)/(?P<target_cos_min>[-+0-9.eE]+)/(?P<target_cos_max>[-+0-9.eE]+))?"
)
SPECTRUM_RE = re.compile(
    r"loco_full_spectrum step=(?P<step>\d+) (?P<name>\w+) layer=(?P<layer>\d+) "
    r"eig_mean=(?P<eig_mean>[-+0-9.eE]+) "
    r"eig_min=(?P<eig_min>[-+0-9.eE]+) "
    r"eig_p01=(?P<eig_p01>[-+0-9.eE]+) "
    r"eig_p50=(?P<eig_p50>[-+0-9.eE]+) "
    r"eig_p99=(?P<eig_p99>[-+0-9.eE]+) "
    r"eig_max=(?P<eig_max>[-+0-9.eE]+) "
    r"eig_cond=(?P<eig_cond>[-+0-9.eE]+) "
    r"gain_mean=(?P<gain_mean>[-+0-9.eE]+) "
    r"gain_min=(?P<gain_min>[-+0-9.eE]+) "
    r"gain_p01=(?P<gain_p01>[-+0-9.eE]+) "
    r"gain_p50=(?P<gain_p50>[-+0-9.eE]+) "
    r"gain_p99=(?P<gain_p99>[-+0-9.eE]+) "
    r"gain_max=(?P<gain_max>[-+0-9.eE]+)"
)


def number(value: str | None):
    if value is None:
        return None
    return float(value)


def parse(path: Path) -> dict[str, list[dict]]:
    rows = {"precond": [], "spectrum": []}
    for line in path.read_text(errors="replace").splitlines():
        if m := PRECOND_RE.search(line):
            step = int(m.group("step"))
            for segment in m.group("body").split(" | "):
                if sm := PRECOND_SEG_RE.fullmatch(segment.strip()):
                    row = {"log": str(path), "step": step}
                    row.update({k: v for k, v in sm.groupdict().items() if k in {"name", "layers"}})
                    for key, value in sm.groupdict().items():
                        if key not in {"name", "layers"}:
                            row[key] = number(value)
                    rows["precond"].append(row)
            continue
        if m := SPECTRUM_RE.search(line):
            row = {"log": str(path)}
            for key, value in m.groupdict().items():
                row[key] = int(value) if key in {"step", "layer"} else (value if key == "name" else number(value))
            rows["spectrum"].append(row)
    return rows


def md(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4e}" if abs(value) < 0.01 or abs(value) >= 100 else f"{value:.4f}"
    return str(value)


def print_table(rows: list[dict], columns: list[str]) -> None:
    print("| " + " | ".join(columns) + " |")
    print("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        print("| " + " | ".join(md(row.get(col)) for col in columns) + " |")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    merged = {"precond": [], "spectrum": []}
    for path in args.logs:
        parsed = parse(path)
        merged["precond"].extend(parsed["precond"])
        merged["spectrum"].extend(parsed["spectrum"])

    if args.json:
        print(json.dumps(merged, indent=2, sort_keys=True))
        return

    if merged["precond"]:
        print("## Preconditioner")
        print_table(
            merged["precond"],
            [
                "step",
                "name",
                "layers",
                "blend",
                "delta_mean",
                "target_delta_mean",
                "cos_mean",
                "target_cos_mean",
            ],
        )
    if merged["spectrum"]:
        print("## Spectrum")
        print_table(
            merged["spectrum"],
            [
                "step",
                "name",
                "layer",
                "eig_p50",
                "eig_p99",
                "eig_cond",
                "gain_p50",
                "gain_p99",
                "gain_max",
            ],
        )


if __name__ == "__main__":
    main()
