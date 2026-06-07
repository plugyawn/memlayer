# Track 3 LocoProp-M Current Verdict - 2026-06-07

Scope: few-step LocoProp-M in the Track 3 simple Muon line, centered on the
seed `3710` step-1600 checkpoint.

This note is the current mechanism read after the K-depth, prefix-specificity,
post-2000, and schedule-only suffix probes.

## Short Answer

The natural true-post `c_fc` LocoProp-M correction does **not** currently tick
externally.

It is locally real:

```text
surface: c_fc only
target_space=post
true_post_grad=1
inner_lr=2e-4
K=5 is externally enough
local loss decreases
correction is applied as a state-decoupled parameter displacement
```

But the active correction does not move validation against alpha-zero:

```text
active K5 @2000:     3.37337
alpha-zero @2000:    3.37338
max active/control delta over 1600..2000: 0.00004
```

Therefore the good `1800->2000` trajectory is schedule/checkpoint/optimizer
state, not the natural K5 `c_fc` LocoProp displacement.

## What We Know

### More Local Steps Are Not The Lever

External K-depth through the prefix:

| lane | 1600 | 1700 | 1800 |
| --- | ---: | ---: | ---: |
| K5, lr2e-4 | 3.48241 | 3.41883 | 3.39870 |
| K8, lr2e-4 | 3.48241 | 3.41884 | 3.39870 |
| K10, lr2e-4 | 3.48241 | 3.41884 | 3.39873 |

Local objective does improve with K:

| K | step | median local loss/loss0 | median corr_norm | median cos |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 1600 | 0.9038 | 4.123e-03 | 0.005 |
| 8 | 1600 | 0.8589 | 5.750e-03 | 0.005 |
| 10 | 1600 | 0.8327 | 6.756e-03 | 0.006 |

Read: more local optimization makes a better local solve, but the validation
curve does not care in this window. Use `K=5` for cheap future screens unless
a new target/surface changes the local optimizer's behavior.

### The Correction Is Too Orthogonal To Explain The Prefix

The prefix effect-size report gives:

```text
median eff_corr/base_step: about 0.005-0.010
median cos: mostly near zero
eff*cos: about -1e-5 to 1.2e-4 of the Muon step
```

That does not mean an orthogonal correction cannot affect future trajectory.
It does mean the observed match between active and alpha-zero is the decisive
external fact: this correction was not doing measurable work.

### Post-2000 LocoProp Does Not Rescue The Slope

From the exact post-prefix 2000 state:

```text
active norm002 LocoProp @2125: 3.36217
no-Loco control @2125:         3.36215 / 3.36216 band
```

The active lane applied a real `2%` base-step correction and still did not beat
control. The local solve still worked, but external trajectory stayed tied.

### Schedule-Only Suffixes Also Failed

From `3.36216 @2125`, the straight-line target for `3.28 @3000` needs
approximately `3.33634 @2400`.

| suffix from 2125 | result |
| --- | ---: |
| floor004 | 3.34512 @2400 |
| floor006 | 3.34630 @2400 |
| floor008 | 3.35557 @2225, stopped |

From `3.33472 @2600`, the straight-line target needs approximately
`3.30736 @2800`.

| suffix from 2600 | result |
| --- | ---: |
| h3300p2 | 3.32745 @2800 |
| PR287 h3075 p1.10 | 3.33727 @2625, spiked |

Read: this is not a simple "raise the LR floor" problem. Cold continuation is
too slow; direct WR-style rewarming spikes the current state.

## What Would Count As LocoProp Ticking

A future LocoProp-family candidate should clear all of these gates before any
long promotion:

```text
1. Same checkpoint and same schedule.
2. Active nonzero correction beats alpha-zero by more than log/validation noise.
3. Same-scale random/orthogonal control does not match the active gain.
4. K=5 or K<=10; no broad K sweep unless K5 locally fails.
5. The result survives at least to the carry decision step, not only the first
   25-50 step validation.
```

A useful minimum external threshold:

```text
delta vs alpha-zero >= 0.002 by 1800 or 2000
```

Anything smaller is below the scale at which our schedule/checkpoint effects
have dominated the story.

## What Not To Spend On Next

Do not spend more immediate GPU time on:

```text
same natural c_fc K8/K10 vs K5
sample_tokens 2048 on the same natural c_fc path
continuing natural c_fc LocoProp after 1800
post-2000 norm002 c_fc on the same state
simple LR floors or direct PR287 suffix switches from the current 2125/2600 states
static c_fc layer subsets before a nonzero all-layer correction beats alpha-zero
```

Static layer subsets can become relevant only after an active all-layer variant
is positive. Otherwise they are optimizing a correction whose external effect
is already zero.

## Remaining Plausible LocoProp Axes

The remaining search should change the correction expression, not just its
iteration count.

1. Prefix normalized `c_fc` correction:
   - same K5 true-post solve;
   - force `norm_target=0.02` or `0.05` from 1600;
   - compare against alpha-zero and same-scale random/orthogonal.

2. Different MLP surface:
   - diagnostic-only `c_proj` first;
   - then small capped active screen if local target loss is sane;
   - this tests whether the useful local objective is on the output projection
     rather than the expansion matrix.

3. Different local target:
   - current true-post target is valid for `c_fc`, but maybe too weakly aligned;
   - a target that includes the actual downstream residual/Muon geometry may be
     necessary for external movement.

4. Local correction plus optimizer-state compatibility:
   - if a new active correction beats alpha-zero in the prefix, only then try a
     suffix schedule that preserves the induced state.

## Current Completion Status

The current answer is a negative mechanism result, not a completed positive
recipe.

Proven:

```text
K=5 is enough for the current local solve.
Natural true-post c_fc LocoProp does not cause the good prefix.
Late natural/normalized c_fc LocoProp does not preserve slope.
Simple LR tail fixes do not rescue the current state.
```

Not yet proven:

```text
which nonzero LocoProp-family correction, if any, beats alpha-zero.
```

So the active goal remains open. The next experiment should be a prefix
specificity screen for a materially different correction expression, not a
suffix schedule probe.
