# Track 3 Post-2000 Landing Requirements - 2026-06-07

Current decision:

```text
Do not spend more runs on the 1600-2000 bracket.
Do not spend more runs on c_fc K-depth, sample tokens, or simple correction scale.
```

The useful question is now narrower:

```text
Can an already-good 3.36/3.32 state be carried to 3.28 by schedule or
late-optimizer state handling?
```

## Is 2000 Too Far Gone?

No, not by absolute loss. It is only too far gone for the suffix behavior we
have already tested.

Required straight-line descent:

| state | target | required drop / 100 steps |
| --- | --- | ---: |
| `3.37333 @2000` | `3.28 @3000` | `0.00933` |
| `3.36216 @2125` | `3.28 @3000` | `0.00939` |
| `3.34512 @2400` | `3.28 @3000` | `0.01085` |
| `3.33472 @2600` | `3.28 @3000` | `0.01368` |

So `2000` and `2125` are still viable states if the run can preserve about
`0.0094` loss drop per 100 steps. `2400` is viable only if the suffix improves
materially. `2600` is already a rescue state for a 3000-step target.

## Corrected Control Read

There are duplicate `control` logs. The older decision table compared some
suffixes against the wrong duplicate and made active LocoProp look better than
it was.

Aligned no-correction replay:

| step | val_loss |
| ---: | ---: |
| 2000 | 3.37335 |
| 2025 | 3.37099 |
| 2050 | 3.36867 |
| 2075 | 3.36657 |
| 2100 | 3.36420 |
| 2125 | 3.36216 |

Visible c_fc LocoProp and random controls from the same suffix family:

| lane | 2000 | 2125 | read |
| --- | ---: | ---: | --- |
| no-correction aligned control | 3.37335 | 3.36216 | best aligned reference |
| floor111 | 3.37335 | 3.36425 | colder and worse |
| floor111 + norm002 K5 | 3.37338 | 3.36429 | worse, matches random |
| floor111 + norm005 K5 | 3.37338 | 3.36430 | worse, matches random |
| floor111 + random002 | 3.37338 | 3.36429 | matches LocoProp |
| floor111 + random005 | 3.37338 | 3.36429 | matches LocoProp |

Conclusion: late additive c_fc LocoProp is not the landing lever in this state.

## What The Known Suffix Does

The aligned no-Loco continuation initially stays close, then loses slope:

| window | drop / 100 steps | target ratio |
| --- | ---: | ---: |
| 2000 -> 2125 | 0.00895 | 0.96x |
| 2125 -> 2400 | 0.00619 | 0.63x |
| 2400 -> 2600 | 0.00343 | 0.32x |
| 2400 -> 3000 | 0.00176 | 0.16x |

By `2400`, the unmodified suffix is no longer close to the required line. The
full no-Loco continuation lands around:

```text
3000: 3.33456
```

This is the core pathology: the state is not too high, but the suffix becomes
slope-starved.

## What Failed

Plain hotter schedule from `2400` failed immediately:

| step | linear3000 no-Loco |
| ---: | ---: |
| 2400 | 3.34500 |
| 2425 | 3.36474 |
| 2450 | 3.36852 |
| 2475 | 3.36917 |
| 2500 | 3.36791 |

Read: this is not simply "LR too low." Global heat shocks the stored optimizer
state.

Delayed bridge schedules from `2125` also failed the `2400 <= 3.3365` gate:

| lane | 2250 | 2400 |
| --- | ---: | ---: |
| `bump150_2250_2650` | 3.35306 | 3.34638 |
| `blend_p15_2250_2650` | 3.35305 | 3.34595 |

Read: delayed global-ish bridge does not change the slope class.

## Next Useful Gate

From a `2400` checkpoint, a useful suffix must visibly change the slope class by
`2600`:

```text
2600 <= 3.3260
```

Also reject any lane that spikes by more than about `0.005` at its first
post-switch validation. The `linear3000` suffix showed that a schedule can be
mathematically hotter but dynamically incompatible.

If a lane clears `2600`, keep it to:

```text
2800 <= 3.3018
3000 <= 3.2800
```

If no lane gets close to `2600 <= 3.3260`, the schedule-only landing hypothesis
from this state is likely dead.

## Most Informative Next Runs

Use `tools/run_track3_suffix_landing_probe.sh` from the `2400` state. Keep
LocoProp off; this is a schedule/optimizer-state question now.

Priority lanes:

```text
control_p2
muon125_2400_2800
adam125_2400_2800
split_muon150_adam085_2400_2800
```

Reason:

```text
global heat failed.
delayed global bridge failed.
late c_fc LocoProp failed.
the remaining cheap axis is optimizer-group LR balance.
```

If those fail, the next LocoProp question should not be more K or scale. It
should change the object:

```text
surface:        c_proj or attention/WR-stack-compatible surface
integration:    first-class fused path, not hook-style c_fc additive suffix
state:          exact WR-stack checkpoint around 2000/2400, not simple-Muon state
```

That is the point at which LocoProp could still "tick": not as a late c_fc
polish step, but as a different local object or as a trajectory creator that
hands the late optimizer a better state.
