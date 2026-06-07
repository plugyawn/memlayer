# Track 3 Suffix Schedule Pivot - 2026-06-07

Decision: stop spending runs on the `1600-2000` bracket.

Reason: active natural true-post `c_fc` LocoProp-M matched alpha-zero by
`2000`, so the visible prefix is not LocoProp-specific. The remaining live
hypothesis is schedule/optimizer-state handling after the run has already
reached the `3.36/3.32` band.

## Required Slope

| state | target | required drop/100 |
| --- | --- | ---: |
| `3.36216 @2125` | `3.28 @3000` | `0.00939` |
| `3.34514 @2400` | `3.28 @3000` | `0.01086` |
| `3.33472 @2600` | `3.28 @3000` | `0.01368` |
| `3.33472 @2600` | `3.28 @3100` | `0.01094` |

Read: a `2600` branch is probably too late for a 3000-step landing unless the
schedule materially improves terminal slope. The best probe point is `2125` or
`2400`.

## What Failed

- Direct LR floors from `2125` did not clear the straight-line gate.
- Direct PR287 from `2600` spiked.
- Stretching to `3300` kept the state smooth but slope-starved.
- Continuing or reactivating the current `c_fc` LocoProp correction was neutral
  or worse.

## Next Probe

Use:

```bash
tools/run_track3_suffix_bridge_probe.sh
```

Default lanes:

```text
cold3000
bump125_2250_2650
bump150_2250_2650
blend_p15_2250_2650
blend_p13_2300_2750
pulse175_2400_2750
```

These are delayed bridge schedules: preserve the cold prefix state, then add a
bounded tail bridge around the region where the curve starts missing target
slope. They explicitly avoid recreating or retesting `1600-2000`.

## Gates

From `2125`, stop the family if no lane is near:

```text
2400 <= 3.3365
2600 <= 3.3150
2800 <= 3.2975
```

From `2400`, stop if no lane is near:

```text
2600 <= 3.3235
2800 <= 3.3018
```

The important metric is not just absolute loss. The lane must preserve slope
without a validation spike at the bridge start.

## 2026-06-07 Suffix Bridge Probe

Prime pod `29eb17f5760742a1a4bab682a23cb8ec` tested the two most direct
`2125 -> 2400` bridge lanes from
`track3_noloco_ckpt2125_seed3710_seed3710_step2125.pt`.

| lane | 2250 | 2400 | gate |
| --- | ---: | ---: | --- |
| `bump150_2250_2650` | 3.35306 | 3.34638 | fail vs 3.33650 |
| `blend_p15_2250_2650` | 3.35305 | 3.34595 | fail vs 3.33650 |

Read: these delayed LR bridges did not change the slope class. The 2250-2400
drop stayed around `0.007` loss, roughly half of the target slope needed to
land at `3.28 @3000`. Do not spend more on this exact `2125` bridge family.
The remaining schedule work should start from an actually later state
(`2400+`) or change the optimizer substrate, not replay the prefix.

## 2026-06-07 Late Linear Probe

Prime pod `432c024310cb4fa79c1ea28036f50d1b` tested a no-LocoProp suffix from
the saved step-2400 state
`track3_short2000_wr3105p120_mult035_hold2400_seed3710_step2400.pt`.

Configuration:

```text
resume_step: 2400
resume_val: 3.34500
train_stop: 2600
lr_schedule: linear
lr_schedule_steps: 3000
locoprop: off
gate: 2500 <= 3.33450
```

Observed:

| step | val_loss |
| ---: | ---: |
| 2400 | 3.34500 |
| 2425 | 3.36474 |
| 2450 | 3.36852 |
| 2475 | 3.36917 |
| 2500 | 3.36791 |
| 2525 | 3.36620 |

Read: the missing suffix is not simply "LR too low after 2400." A true
3000-horizon linear tail shocks this optimizer/model state immediately. The
productive state appears to require a compatible late optimizer substrate or a
careful cold-to-hot transition that does not disturb the stored optimizer
dynamics. Do not repeat plain hotter-linear suffixes from this 2400 checkpoint.
