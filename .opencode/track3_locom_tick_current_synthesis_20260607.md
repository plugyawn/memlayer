# Track 3 LocoProp-M Current Synthesis - 2026-06-07

Scope:

```text
simple Track 3 Muon substrate
seed3710 step-1600 checkpoint family
c_fc-only LocoProp-M
true-post local target
separate additive parameter displacement
K in {5,8,10}
```

This is the current source-of-truth read for the "what makes LocoProp tick?"
question. It supersedes the earlier optimistic interpretation that the good
`1800->2000` slope was caused by the active natural c_fc LocoProp correction.

## Answer

For this exact implementation, LocoProp-M does not currently tick.

The local solve is real: K5/K8/K10 reduce the layerwise local objective. But
the applied correction is too small, too sideways relative to the Muon update,
and experimentally indistinguishable from alpha-zero/no-correction controls.

The thing that ticks in the saved trajectories is the schedule/checkpoint state,
not the natural K5 c_fc additive displacement.

## Core Evidence

### K-depth is answered

The K-depth screen from the same step-1600 state:

```text
K5:  3.48241 @1600 -> 3.39870 @1800
K8:  3.48241 @1600 -> 3.39870 @1800
K10: 3.48241 @1600 -> 3.39873 @1800
```

More K improves the local objective but does not move validation through the
prefix screen. K5 is externally enough for this branch. Spending more on K8/K10
alone is not justified.

### The natural correction is externally neutral

Same-harness active K5 vs alpha-zero/no-correction through 2000:

```text
active K5 @1800:  3.39872
alpha-zero @1800: 3.39873

active K5 @1900:  3.38478
alpha-zero @1900: 3.38478

active K5 @2000:  3.37337
alpha-zero @2000: 3.37338

max shared-screen absolute delta: 0.00004
final control-active delta @2000: 0.00001
```

This is the decisive causal negative: the good prefix/suffix trajectory survives
when the LocoProp correction is computed diagnostically but applied with zero
scale.

### The correction budget is tiny and mostly lateral

Typical natural K5/K8/K10 applied correction:

```text
median correction/base Muon step: about 0.006-0.020
median cosine with Muon descent: about 0.005-0.020
descent-aligned component: about 0.00005-0.00012 of the base step
```

To get even a 1 percent base-step-aligned contribution by scaling this vector,
the total correction would need to become around `0.5x-2.5x` the Muon step in
the observed windows. That is not a small LocoProp nudge; it is a large mostly
sideways perturbation.

### Visible-scale c_fc also failed

From the exact step-2000 state:

```text
step 2000 control:          3.37335
step 2000 norm002_k5:       3.37338
step 2000 norm005_k5:       3.37338
step 2000 random_norm002:   3.37338
step 2000 random_norm005:   3.37338

step 2125 control:          3.36216
step 2125 norm002_k5:       3.36429
step 2125 norm005_k5:       3.36430
step 2125 random_norm002:   3.36429
step 2125 random_norm005:   3.36429
```

Forcing the same c_fc correction to a visible `2%` or `5%` of the base step
does not help. It matches same-scale random and trails the no-correction suffix.

### Sample size was not the blocker

The 1024 vs 2048 sample-token comparison reduced some diagnostic noise but
matched validation on the corrected schedule. That rules out "just sample more"
for this exact branch.

## What It Would Mean For LocoProp To Tick

A future LocoProp-family run only counts as positive if it passes this gate:

```text
same checkpoint
same schedule
same harness
active nonzero correction beats alpha-zero by >= 0.001 at the decision point
random/same-scale perturbation does not match the gain
```

For the current prefix, the decision point is step `2000`, because `1900->2000`
is still healthy and target-positive. For suffix-only probes, the decision
point is the first branch gate after the checkpoint, usually `2125`, `2250`,
`2400`, or `2600` depending on the start state.

Anything that improves both active and alpha-zero equally is schedule/state
alpha, not LocoProp alpha.

## Ruled-Out Knobs

Do not spend more GPU on these as isolated changes:

```text
more K on c_fc true-post additive: K5/K8/K10 tie externally
more sample tokens on the same path: 1024 and 2048 matched validation
natural c_fc true-post correction: alpha-zero matches active
visible 2%/5% c_fc correction: worse than control and matches random
post-2000 same c_fc correction: slope-starved versus no-correction
random same-shape perturbation: no better than no-correction
```

## Layer Read

The local gate is broad and moving. It is not "all layers" in a fixed way.

K5 layer-health screen:

```text
strong local-gain layers:      2,7,8,9,10
robust cross-K core:           7,8,9,10
expanded plausible core:       6,7,8,9,10
risky / inconsistent:          2,11
weak but often accepted:       0,1,5,6
```

Layer-subset probes are currently deprioritized because the all-layer nonzero
correction failed the alpha-zero gate. They only become worth running again if
a materially different LocoProp expression first beats alpha-zero.

## Still-Open LocoProp Directions

These would be genuinely different hypotheses, not repeats of the dead c_fc
line:

```text
surface:
  c_proj, attention V, Q/K/O, or selected robust MLP layers only

object:
  not the same true-post c_fc additive displacement;
  for example a correction built from a different local target/residual

integration:
  not the same state-decoupled tiny additive update;
  for example a separate optimizer-state-aware local correction, or a metric
  update on a surface where alpha-zero does not match active

state:
  exact WR-stack suffix checkpoint rather than the already-answered simple
  Muon 1600->2000 prefix
```

The first run for any reopened LocoProp object should be a cheap specificity
gate, not a long landing attempt.

## Current Speedrun Read

The good known slope is schedule/checkpoint driven:

```text
1800->1900: healthy
1900->2000: healthy and enough for a 3.28 landing if preserved
2000->2125: starts cooling
2400+: mostly landing/scheduler problem
```

So the near-term WR path is not to keep pushing this c_fc LocoProp correction.
It is to preserve the already-good post-prefix slope using schedule/optimizer
state. LocoProp should only re-enter after a new surface/object/integration
beats alpha-zero under a matched gate.

## Minimal Next LocoProp Experiment If Reopened

Do not launch broad sweeps. The next LocoProp-specific experiment should be:

```text
checkpoint: exact step-1600 or exact WR-stack suffix checkpoint
lanes:
  alpha-zero
  active new LocoProp object
  same-scale random
  optional orthogonalized correction
gate:
  active beats alpha-zero by >= 0.001
  random/orthogonal do not match
stop:
  kill by the first decision screen if the gate fails
```

If that gate fails, the run can still be useful for schedule debugging, but it
is not evidence that LocoProp-M is working.
