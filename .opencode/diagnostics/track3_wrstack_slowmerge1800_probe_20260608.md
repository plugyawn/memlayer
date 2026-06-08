# Track 3 WR Optimizer2 Slow-Merge From Step 1800 Probe - 2026-06-08

## Purpose

Test whether the large handoff shock from switching the LocoProp/coldp2 step-1800
model into the current-record WR optimizer2 stack can be avoided by ramping only
WR optimizer2 learning rates from a small multiplier to full strength.

This directly probes the hypothesis that the previous WR-stack handoff failed
mainly because the full 324-float-tensor optimizer2 state/update was introduced
too abruptly.

## Provenance

- Local branch: `codex/track3-locom-clean-20260606`
- Local HEAD at launch: `b7b46c1`
- Pod: `68af4a7f8f23446ca43b152c2958abb9`
- GPU: Prime H100 SXM5 spot, datacrunch, `$1.14/hr`
- Checkpoint: `/Users/progyan/speedrun/tmp/prime_wrstack_from1800_checkpoints/track3_k5_coldp2_seed3710_to1800_seed3710_step1800.pt`
- Remote logs pulled to:
  `.opencode/current_track3_ledger_20260608_logs/wrslowmerge1800_68af4a7f8f23446ca43b152c2958abb9/remote_logs/`

The run loaded model + Adam state from the step-1800 checkpoint, restored RNG,
advanced data, and intentionally did not load the old optimizer2 state. WR
optimizer2 was freshly initialized from the current-record source.

## Results

Baseline references from the immediately previous same-1800 probe:

| Lane | 1875 | 2000 | 2125 | 2250 | 2500 |
| --- | ---: | ---: | ---: | ---: | ---: |
| simple/coldp2 continuation | 3.38816 | 3.37335 | 3.36214 | 3.35305 | 3.34113 |
| hard WR-stack switch | 3.47212 | 3.45648 | 3.43429 | 3.41066 | 3.36644 |

Slow-merge probe:

| Lane | opt2 LR multiplier | 1875 | 2000 | 2125 | 2250 |
| --- | --- | ---: | ---: | ---: | ---: |
| alpha20 | 0.20 -> 1.00 over 1800:2250 | 3.41953 | 3.41529 | 3.41089 | 3.40481 |
| alpha00 | 0.00 -> 1.00 over 1800:2250 | 3.41437 | 3.41028 | - | - |

`alpha20` was manually stopped after the bad 2125/2250 behavior. `alpha00`
was stopped at 2000 after also showing the same shock/stall pattern.

## Interpretation

The slow optimizer2 LR ramp reduces the catastrophic hard-switch shock, but it
does not restore the useful simple/coldp2 trajectory. Both ramps land in a bad
middle regime: better than hard WR-state injection, but still far behind the
state they are supposed to improve.

This falsifies the narrow "just introduce WR optimizer2 more slowly from the
LocoProp/coldp2 1800 state" hypothesis. The issue is not only LR handoff
sharpness. The WR optimizer2 machinery appears to require a compatible earlier
trajectory/state, not just a late gradual activation on top of the low-energy
LocoProp/coldp2 state.

The next useful direction is not another scalar opt2 ramp from 1800. It should
either:

1. build breadth earlier before the LocoProp/coldp2 state becomes low-energy, or
2. find a suffix operation that changes subspace/rank directly rather than
   rescaling the WR optimizer2 update.

## Cleanup

The pod was terminated after logs were pulled. `prime pods list` returned zero
active pods.
