# Track 3 LocoProp-M Tick Requirements - 2026-06-07

Current scope:

```text
simple Track 3 Muon substrate
seed3710 step-1600 checkpoint
c_fc LocoProp-M, true-post local target, K=5-10
```

## What We Now Know

The good prefix window is real:

```text
1900: 3.38478
2000: 3.37337
drop: 0.01141 per 100 steps
```

This makes step 2000 a real branch point, not a dead state:

```text
target from 2000: 3.37337 -> 3.28000 by 3000
required drop:    0.00934 per 100 steps
observed 1900-2000 drop / required: about 1.22x
```

But the slope starts failing immediately after that:

```text
2000->2100: 0.00914 per 100, about 0.98x required
2100->2125: 0.00828 per 100, about 0.89x required
```

So the suffix problem is specifically preserving the 1900-2000 descent
rate after step 2000. Pure 2950+ rescue is too late.

But it is not caused by the natural K5 c_fc LocoProp correction:

```text
active K5 @2000:      3.37337
alpha-zero @2000:     3.37338
max shared-screen gap: 0.00004
```

So the current natural correction does not tick externally, even though it is
locally sane.

## Why The Natural Path Washes Out

Implementation:

```text
prepare_locoprop_m:
  solve local c_fc matching problem
  store W - W0 as _loco_corr if local loss decreases and cosine gate passes

_locom_apply_owned_param_:
  base_step_norm = ||Muon update|| * lr
  scale = 1 by default
  optional norm_target / norm_to_base / norm_cap changes scale
  p.add_(corr, alpha=scale * alpha)
```

Natural K5 applied scale:

```text
median correction/base_step: ~0.005-0.010
median cosine with Muon descent: mostly ~0.0-0.015
base-descent-aligned component: about -1e-5 to 1.2e-4 of the Muon step
```

This means the natural correction is both small and mostly lateral relative to
the base Muon step. The alpha-zero match proves that any feature-conditioned
lateral component at this natural scale did not measurably change validation.

## Ruled Out

```text
more local iterations alone:
  K5, K8, and K10 tie externally through 1800

more sample tokens alone:
  1024 -> 2048 matched validation on the corrected coldp2 schedule

same c_fc correction later:
  norm_target=0.02 from the exact step-2000 state matched/slightly trailed
  no-correction, despite successful local solves

natural K5 prefix:
  active and alpha-zero match through 2000
```

## Necessary Condition For A Positive LocoProp Mechanism

Any future LocoProp-family claim must first pass this gate:

```text
same checkpoint
same schedule
same harness
active nonzero correction beats alpha-zero by >= 0.001 at 2000
random/scheduler control does not match the gain
```

If it does not beat alpha-zero, it is not evidence for LocoProp. It may still
be a schedule/optimizer-state improvement.

## Next Minimal Probe

The unresolved branch is scale, not K-depth:

```text
tools/run_track3_locom_prefix_scale_probe.sh
```

Lanes:

```text
noloco:        same harness, alpha=0
active_k5:     natural K5 c_fc correction
norm002_k5:    same direction normalized to 2% of base step
norm005_k5:    same direction normalized to 5% of base step
random_norm002: same-shape random 2% control
random_norm005: same-shape random 5% control
```

Decision:

```text
norm002/norm005 beats alpha-zero and random:
  natural correction was too small; tune scale/window/layers.

norm002/norm005 match alpha-zero:
  c_fc true-post direction is not the causal lever in this state.

same-scale random matches active:
  effect is generic perturbation/noise, not local solve.

norm005 hurts while norm002 matches:
  direction may be weakly valid but scale window is very narrow; do not promote
  without a positive replicate.
```

## Current Synthesis

The thing that currently "ticks" is the cold schedule/checkpoint trajectory,
not the natural LocoProp displacement. The only remaining way for this exact
c_fc LocoProp idea to survive is if a deliberately visible correction scale
beats alpha-zero in the prefix. If that fails, the next search should move to a
different LocoProp expression or surface rather than spending more on K,
sample tokens, or suffix-only tuning.

For suffix work, the target is narrower: start from the saved/recreated step
2000 state and preserve at least the required line to step 3000. The current
post-2000 ladder therefore has matched 2% and 5% random controls; any active
LocoProp win must beat the same-scale perturbation, not just the no-correction
suffix.
