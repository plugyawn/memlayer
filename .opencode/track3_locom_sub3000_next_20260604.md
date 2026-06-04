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

4. Prime self-gated suffix, MassedCompute H100 PCIe:

```text
resume=track3_short2000_wr3105p120_mult035_hold2400_seed3710_step2400.pt
schedule=pr287 h3105 p1.20
LR multiplier=0.35 through 2450, fade to full by 2750
LocoProp active windows=0:1800 only

2400: 3.34502
2425: 3.34337
2450: 3.34138
2475: 3.34061
2500: 3.34023
2525: 3.34044
2550: 3.34021
2575: 3.33976
2600: 3.33989
verdict: stable but flat; failed 2600 gate against old slow-fade 3.33852
```

5. Same 2400 checkpoint and tail, late LocoProp reactivated:

```text
LocoProp active windows=0:1800,2400:2700
cap=0.20, K=4

2400: 3.34502
2425: 3.34345
2450: 3.34144
2475: 3.34071
2500: 3.34032
verdict: active corrections were consistently slightly worse than scheduler-only;
failed stricter 2500 gate. Late online LocoProp on this 2400 state is not the
missing tail.
```

## Next targeted run

Status: executed and failed. Do not rerun this exact suffix.

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

## Next WR-stack overlay gate

The 2400 suffix branch is now closed. The next non-redundant spend is to test
whether LocoProp-M helps the current-record optimizer substrate after the
meaningful `900-1600` phase, using the hookless auxiliary capture path so the
main WR training graph stays compiled.

Run:

```text
script=.opencode/prime_scripts/wr_record_locom_aux_k5_lr1e3_nogate2000_seed3710_gated.sh
source=records/track_3_optimization/results/20260509_contra_soft_muon/03c36e81-e2e5-4916-bf16-0141999b1dbb.txt
schedule=WR current-record h3105/p1.20 source
LocoProp=aux c_fc, K=5, inner_lr=1e-3, cap=0.20, no accept/reject gate
train_steps=2000
seed=3710
```

Why this is not redundant:

```text
500-step aux screens were slightly worse, but 500 is before the phase where the
simple-Muon LocoProp prefix visibly separated. The exact-WR-state suffix probes
from 2000 were neutral/worse, but those did not test co-training through the
phase that could shape the model trajectory.
```

Automated gates:

```text
1000 <= 3.6650
1250 <= 3.6060
1500 <= 3.5500
1625 <= 3.5280
1750 <= 3.5000
1875 <= 3.4750
2000 <= 3.4450
```

Interpretation:

```text
If it fails before 1500, WR-stack LocoProp is actively hurting before the
interesting phase and should not be extended. If it survives but is not near or
ahead of WR source by 2000, the useful simple-Muon LocoProp mechanism does not
transfer to the current-record substrate. If it is ahead by 2000, promote to a
terminal-tail branch with current-record Soft-Muon/Contra/SOAP intact.
```
