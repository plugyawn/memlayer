#!/usr/bin/env python3
"""Watch a Track 3 training log and stop the run when loss gates fail."""

from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path


VAL_RE = re.compile(
    r"step:(?P<step>\d+)/(?P<total>\d+)\s+val_loss:(?P<loss>[0-9.eE+-]+)\s+"
    r"train_time:(?P<time>[0-9.]+)(?P<unit>ms|s)\s+step_avg:(?P<avg>[0-9.]+)ms"
)


def parse_gate(spec: str) -> tuple[int, float]:
    fields = spec.split(":")
    if len(fields) != 2:
        raise argparse.ArgumentTypeError("gate must be STEP:MAX_LOSS")
    try:
        step = int(fields[0])
        max_loss = float(fields[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("gate must be STEP:MAX_LOSS") from exc
    if step < 0:
        raise argparse.ArgumentTypeError("gate step must be nonnegative")
    return step, max_loss


def read_val_points(path: Path) -> dict[int, float]:
    if not path.exists():
        return {}
    points: dict[int, float] = {}
    text = path.read_text(errors="replace")
    for line in text.splitlines():
        match = VAL_RE.search(line)
        if match:
            points[int(match["step"])] = float(match["loss"])
    return points


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def kill_process_group(pid: int, grace_s: float) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace_s
    while time.monotonic() < deadline:
        if not process_alive(pid):
            return
        time.sleep(0.5)
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def append_status(path: Path | None, message: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {message}\n"
    if path is None:
        print(line, end="", flush=True)
        return
    with path.open("a") as handle:
        handle.write(line)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--pid", required=True, type=int, help="process group leader pid")
    parser.add_argument(
        "--max-loss",
        action="append",
        default=[],
        type=parse_gate,
        metavar="STEP:MAX_LOSS",
        help="fail and terminate when the validation loss at STEP exceeds MAX_LOSS",
    )
    parser.add_argument("--poll-interval", type=float, default=15.0)
    parser.add_argument("--grace-seconds", type=float, default=20.0)
    parser.add_argument("--status-file", type=Path)
    args = parser.parse_args()

    gates = dict(args.max_loss)
    if not gates:
        raise SystemExit("--max-loss is required")

    seen: set[int] = set()
    append_status(args.status_file, f"gate_watcher_started pid={args.pid} gates={gates}")

    while process_alive(args.pid):
        points = read_val_points(args.log)
        for step in sorted(gates):
            if step in seen or step not in points:
                continue
            seen.add(step)
            loss = points[step]
            max_loss = gates[step]
            if loss > max_loss:
                append_status(
                    args.status_file,
                    f"gate_failed step={step} loss={loss:.5f} max_loss={max_loss:.5f}; terminating",
                )
                kill_process_group(args.pid, args.grace_seconds)
                return 42
            append_status(args.status_file, f"gate_passed step={step} loss={loss:.5f} max_loss={max_loss:.5f}")
        time.sleep(args.poll_interval)

    points = read_val_points(args.log)
    missing = [step for step in sorted(gates) if step not in points]
    if missing:
        append_status(args.status_file, f"gate_watcher_exit_missing_gates steps={missing}")
        return 0
    append_status(args.status_file, "gate_watcher_exit_all_gates_seen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
