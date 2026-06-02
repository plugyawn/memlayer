#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


SEPARATOR = "\n" + "=" * 100 + "\n"


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"pattern not found: {old!r}")
    return text.replace(old, new, 1)


def generate(source: Path, output: Path, *, train_steps: int | None, schedule_steps: int | None, val_every: int | None) -> None:
    text = source.read_text()
    if source.suffix == ".txt" and SEPARATOR in text:
        text = text.split(SEPARATOR, 1)[0]

    if train_steps is not None:
        text = re.sub(
            r"(?m)^FINAL_TRAIN_STEPS = \d+\s*$",
            f"FINAL_TRAIN_STEPS = {train_steps}",
            text,
            count=1,
        )
        if f"FINAL_TRAIN_STEPS = {train_steps}" not in text:
            raise RuntimeError("FINAL_TRAIN_STEPS pattern not found")

    if schedule_steps is not None:
        text = re.sub(
            r"(?m)^FINAL_SCHEDULE_STEPS = \d+\s*$",
            f"FINAL_SCHEDULE_STEPS = {schedule_steps}",
            text,
            count=1,
        )
        if f"FINAL_SCHEDULE_STEPS = {schedule_steps}" not in text:
            raise RuntimeError("FINAL_SCHEDULE_STEPS pattern not found")

    text = replace_once(text, "mbs = 64\n", 'mbs = int(os.environ.get("TRACK3_MBS", "64"))\n')
    if val_every is not None:
        text = replace_once(text, "val_regular_interval = 125\n", f"val_regular_interval = {val_every}\n")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--train-steps", type=int)
    parser.add_argument("--schedule-steps", type=int)
    parser.add_argument("--val-every", type=int)
    args = parser.parse_args()
    generate(
        Path(args.source),
        Path(args.output),
        train_steps=args.train_steps,
        schedule_steps=args.schedule_steps,
        val_every=args.val_every,
    )


if __name__ == "__main__":
    main()
