# Track 3 LocoProp-M c_proj Gate Ready - 2026-06-07

Reason:

```text
c_fc true-post additive LocoProp-M is answered negative:
active K5 and alpha-zero match through 2000.
```

The next LocoProp-specific question must change the object. The smallest
prepared change is `TRACK3_LOCOM_SURFACE=proj`, which solves a local linear
problem for `mlp.proj.weight`:

```text
features: post = relu(fc(x))^2
output:   y = proj(post)
target:   y - gamma * dL/dy
update:   W_proj <- W_proj + alpha * correction
state:    separate additive parameter displacement after the Muon step
```

This is not full `3072 x 3072` Gram/inverse preconditioning. It is K-step local
optimization on the sampled projection problem, so it is slower than c_fc but
still a narrow Track 3 LocoProp-M probe.

## Code Path

Generator support:

```text
tools/make_track3_locoprop_m.py
TRACK3_LOCOM_SURFACE=fc      # default, old behavior
TRACK3_LOCOM_SURFACE=proj    # new c_proj local objective
```

Fail-fast runner:

```text
tools/run_track3_locom_proj_specificity.sh
```

Dry-run validation completed:

```text
TRACK3_DRY_RUN=1 MODE=pair     tools/run_track3_locom_proj_specificity.sh
TRACK3_DRY_RUN=1 MODE=controls tools/run_track3_locom_proj_specificity.sh
python3 -m py_compile tools/make_track3_locoprop_m.py
bash -n tools/run_track3_locom_proj_specificity.sh
```

## First GPU Command

On an already-prepared H100/GH200 pod with the step-1600 checkpoint copied:

```bash
MODE=pair \
TRACK3_PROJ_SPEC_LOG_DIR=/root/prime_track3_locom_proj_specificity_logs \
bash tools/run_track3_locom_proj_specificity.sh
```

This runs only:

```text
proj alpha-zero
proj active K5 natural scale
```

Do not run `MODE=controls` unless active beats alpha-zero by a material margin.

## Gate

Promote only if:

```text
active proj beats alpha-zero by >= 0.001 at 2000
and the difference is already visible by 1800 or persists through 1900->2000
```

If the pair gate passes, run controls:

```bash
MODE=controls \
TRACK3_PROJ_SPEC_LOG_DIR=/root/prime_track3_locom_proj_specificity_logs \
bash tools/run_track3_locom_proj_specificity.sh
```

Controls must not match active:

```text
random_norm002
orthogonal_norm002
```

If controls match active, the effect is not projection LocoProp-specific.

## Kill Rules

```text
active ~= alpha-zero through 1800:
    stop; c_proj natural scale is also neutral.

active worse by >= 0.001 by 1800:
    stop; do not let it run to 3000.

active beats alpha-zero but random/orthogonal matches:
    not LocoProp-specific; treat as perturbation/schedule effect.

active beats alpha-zero and controls do not:
    this is a real new LocoProp object; then tune K, inner_lr, norm cap, and
    layer subset.
```

## Why c_proj Is The Next Surface

It is materially different from c_fc:

```text
c_fc local target: nonlinear post-activation matching through relu^2
c_proj local target: linear output residual matching
```

That makes the local solve closer to the LocoProp-S affine primitive. It also
touches the part of the MLP that receives heavy-tailed `relu^2` features, which
is a plausible place for right-side feature geometry to matter.

It is not free:

```text
feature dimension: 3072
weight shape:      768 x 3072
sample bandwidth:  higher than c_fc
```

So the first test is a specificity gate, not a landing run.
