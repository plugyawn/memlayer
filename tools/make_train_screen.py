#!/usr/bin/env python3
"""Create a short-run train_gpt.py screen from the canonical training script."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def replace_once(text: str, pattern: str, repl: str, name: str) -> str:
    text, count = re.subn(pattern, repl, text, count=1)
    if count != 1:
        raise SystemExit(f"failed to replace {name}; pattern matched {count} times")
    return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="train_gpt.py")
    parser.add_argument("--output", default="train_gpt_screen.py")
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--extension", type=int, default=0)
    parser.add_argument("--val-every", type=int, default=20)
    parser.add_argument(
        "--warmup",
        default="0,1,8,18,19,20,21,24,38,39,40,41,48,58,59,60",
        help="Comma-separated warmup step list.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.source)
    output = Path(args.output)
    warmup_steps = ", ".join(str(int(part.strip())) for part in args.warmup.split(",") if part.strip())

    text = source.read_text()
    text = replace_once(
        text,
        r"num_scheduled_iterations: int = \d+",
        f"num_scheduled_iterations: int = {args.steps}",
        "num_scheduled_iterations",
    )
    text = replace_once(
        text,
        r"num_extension_iterations: int = \d+",
        f"num_extension_iterations: int = {args.extension}",
        "num_extension_iterations",
    )
    text = replace_once(
        text,
        r"val_loss_every: int = \d+",
        f"val_loss_every: int = {args.val_every}",
        "val_loss_every",
    )
    text = replace_once(
        text,
        r"warmup_steps = sorted\(\{0, 1\} \| \{s \+ offset for s in transition_steps for offset in \[-2, -1, 0, 1\] if s \+ offset >= 2\}\)",
        f"warmup_steps = sorted({{{warmup_steps}}})",
        "warmup_steps",
    )
    output.write_text(text)
    print(f"wrote {output} from {source} with steps={args.steps} val_every={args.val_every}")


if __name__ == "__main__":
    main()
