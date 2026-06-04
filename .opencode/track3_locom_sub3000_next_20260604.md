# Track 3 LocoProp-M Sub-3000 Next Gate

Date: 2026-06-04

## Current state

The useful LocoProp-M evidence is model-trajectory evidence, not late online
correction evidence.

Known good mid-run state:

```text
checkpoint=track3_short2000_wr3105p120_mult035_hold2400_seed3710_step2400.pt
local=/Users/progyan/speedrun/tmp/prime_recover2000_checkpoints/track3_short2000_wr3105p120_mult035_hold2400_seed3710_step2400.pt
sha256=8e1203d36104540836de0d74dcd7d70f9ba2a5a28d701afe047e50709bff72cb
loss=3.34502 @2400
```

This is not enough by itself. The line still needs a tail that preserves the
LocoProp prefix advantage and then accelerates instead of stalling.

## What failed

1. Hard import of current-record WR optimizer state failed:

```text
start: 3.38827 @2000
mature WR optimizer + optimizer2 momentum scale 0.5:
  2125: 3.43293
  2250: 3.41426
  2375: 3.39274
fresh WR optimizer:
  2125: 3.43373
```

This rules out direct WR-state splicing as the next spend.

2. Late LocoProp reactivation at cap 0.10 was exact parity with no
reactivation:

```text
reactivation:   2500: 3.33968
no reactivation:2500: 3.33968
```

So the next lever should be the scheduler/optimizer tail, not more late
LocoProp compute.

3. From the saved 2400 checkpoint:

```text
stable slow fade to full by 2900:
  2500: 3.34155
  2600: 3.33852
  verdict: stable, too cold

immediate fade to full by 2700:
  2500: 3.34405
  verdict: gentler than 2600 fade but already turning upward

immediate fade to full by 2600:
  2500: 3.34748
  verdict: too hot / shocky
```

## Next targeted run

Run exactly one suffix first:

```text
script=.opencode/prime_scripts/suffix_from2400_wr3105p120_hold2450_fade2750.sh
resume=track3_short2000_wr3105p120_mult035_hold2400_seed3710_step2400.pt
schedule=pr287 h3105 p1.20
LR multiplier=0.35 through 2450, then fade to full by 2750
LocoProp active windows=0:1800 only
```

The script runs under `tools/watch_track3_gates.py`, so the process group is
terminated automatically if any observed gate fails. This is meant to protect
the next GPU session from drifting into a full run after the 2500/2600 evidence
already answers the question.

Multiplier comparison:

```text
step  slow2900  fade2700  candidate
2400  0.3500    0.3500    0.3500
2450  0.4150    0.4583    0.3500
2500  0.4800    0.5667    0.4583
2550  0.5450    0.6750    0.5667
2600  0.6100    0.7833    0.6750
2650  0.6750    0.8917    0.7833
2700  0.7400    1.0000    0.8917
2750  0.8050    1.0000    1.0000
2800  0.8700    1.0000    1.0000
```

Why this is the right next spend: it is colder than both shocky immediate
release variants through 2500, then warmer than the stable slow-fade after
2550. It directly tests whether the missing piece is delayed release rather
than WR-state import or renewed LocoProp corrections.

## Kill gates

Do not let this become a full run unless it earns it.

```text
2500:
  kill if > 3.3430
  interpretation: delayed release failed to preserve the 2400 lead

2600:
  kill unless clearly better than 3.33852
  interpretation: if it cannot beat the old stable slow-fade line here, it is
  not the sub-3000 path

2750:
  continue only if <= 3.315-ish
  interpretation: it must start resembling a WR tail, not merely preserve a
  nicer mid-run state

2875:
  continue only if <= 3.288-ish
  interpretation: otherwise there is no plausible <3000 crossing
```

## Launch prerequisites

The pod must already have, or receive, the local 2400 checkpoint:

```text
/home/ubuntu/.cache/track3_checkpoints/track3_short2000_wr3105p120_mult035_hold2400_seed3710_step2400.pt
```

Do not launch with the current Prime balance unless there is enough budget to
reach at least the 2600 gate.
