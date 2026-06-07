# Track 3 Suffix Schedule Pivot - 2026-06-07

Current user decision:

```text
Stop spending runs on the 1600-2000 bracket.
Treat the remaining problem as a landing schedule from an already-good state.
```

The live hypothesis is:

```text
There exists a suffix schedule that carries a 3.36/3.32 state to 3.28.
```

## Why This Is Plausible

The absolute loss is not the blocker:

| state | target | required drop / 100 steps |
| --- | ---: | ---: |
| `3.36216 @2125` | `3.28 @3000` | `0.00939` |
| `3.34512 @2400` | `3.28 @3000` | `0.01085` |
| `3.33472 @2600` | `3.28 @3000` | `0.01368` |

Those numbers are not impossible. The problem is that the observed suffix loses
slope as the LR cools.

## What Not To Run

Do not run more broad probes in:

```text
1600-2000 prefix/bracket
c_fc K-depth
c_fc sample_tokens
c_fc random/orthogonal/parallel scale controls
```

Those answered mechanism questions but did not solve the landing.

## What Already Failed

Plain global heat from 2400 failed:

| step | linear3000 no-Loco |
| ---: | ---: |
| 2400 | 3.34500 |
| 2425 | 3.36474 |
| 2450 | 3.36852 |
| 2475 | 3.36917 |
| 2500 | 3.36791 |

Read: jumping from the cold p2 tail directly to a much hotter global linear
suffix shocks the stored optimizer state.

The old `floor111` family also failed because it was an immediate high floor.
It did not test a continuity-preserving floor.

## New Schedule Lever

Add `TRACK3_LR_MIN_ETA_WINDOWS`:

```text
start:ramp_end:hold_end:fade_end:eta
```

This is an LR floor, not a multiplier. It ramps the minimum eta smoothly, then
applies:

```python
eta = max(base_eta, static_min_eta, window_floor_eta)
```

Primary examples:

```text
2400:2500:3000:3000:0.04
2400:2500:3000:3000:0.06
2400:2600:3000:3000:0.06
```

Why this is the right form:

```text
p2 eta at 2400 on a 3000 schedule is 0.04.
So a ramped floor can start without an immediate LR jump.
By 2600, p2 eta is only about 0.0178.
By 2800, p2 eta is only about 0.0044.
```

The floor directly targets the tail collapse while avoiding the first-step
validation spike from the linear suffix.

## Gate

From the 2400 checkpoint:

```text
2600 <= 3.3260
2800 <= 3.3018
3000 <= 3.2800
```

Reject immediately if the first post-switch validation spikes by more than
about `0.005`.

## Launcher

Use:

```bash
TRACK3_SUFFIX_CHECKPOINT=/home/ubuntu/.cache/track3_checkpoints/track3_locom_2000_control_seed3710_seed3710_step2400.pt \
TRACK3_SUFFIX_LANES=control_p2,floor004_r2500,floor006_r2500,floor006_r2600 \
bash tools/run_track3_suffix_landing_probe.sh
```

The defaults now match this lane set. The group-bump lanes are still available
for deliberate follow-up, but they are no longer the default spend.
