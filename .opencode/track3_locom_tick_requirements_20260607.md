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

visible c_fc correction scale:
  norm_target=0.02 and norm_target=0.05 from the exact step-2000 state both
  trailed the no-correction suffix and matched same-scale random perturbations
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

## Scale Probe Result

The scale branch is now answered for this exact c_fc true-post variant.

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

The active LocoProp direction did not beat alpha-zero/no-correction. It also
did not beat same-scale random. Normalizing the correction to a visible 2% or
5% of the base step made the suffix worse by about 0.002 at step 2125.

Decision:

```text
close current c_fc true-post K5-10 additive line.
do not spend more GPU on K-depth, sample tokens, or simple correction scale.
only reopen LocoProp if the object/surface/integration changes.
```

## Current Synthesis

The thing that currently "ticks" is the cold schedule/checkpoint trajectory,
not the natural LocoProp displacement. The visible-scale probe failed too, so
this exact c_fc LocoProp expression is not the causal lever in the current
state.

For suffix work, the target is narrower: start from the saved/recreated 2000 or
2400 state and preserve enough slope to step 3000. A useful next run should
change the landing schedule or optimizer-group LR balance; it should not spend
more budget on the 1600-2000 bracket or on c_fc K-depth.

If LocoProp is reopened, the test must change at least one of:

```text
surface:        not only c_fc
object:         not true-post additive c_fc displacement
integration:    not a state-decoupled additive correction at 2-5% base norm
state:          exact WR-stack suffix checkpoint, not the already-answered prefix
```
