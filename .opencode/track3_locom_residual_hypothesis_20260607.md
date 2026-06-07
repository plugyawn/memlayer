# Track 3 LocoProp-M Residual Hypothesis 2026-06-07

## Current State

The active Prime pod is intentionally still up:

```text
pod_id: 43ad3702f6e843d397f1e5e2d1d6dbb1
name: oc-main-track3-tailcopy-h100sxm-20260607-1515
gpu: NVIDIA H100 80GB HBM3
```

At the last direct SSH check it was idle, not terminated:

```text
gpu util: 0%
gpu memory: 0 MiB
```

The tail-end checks already completed on this pod. The pod remains warm only
because the next useful experiment can reuse the copied checkpoint, dataset
cache, and pinned stack.

## Facts From The Tail Probes

The clean reproduced branch points are:

```text
step 1600 checkpoint: 3.48241
step 2000 checkpoint: 3.37335-ish
step 2500 cold branch: 3.34114
```

From the 2500 checkpoint, the cold terminal suffix is almost flat:

```text
2500: 3.34114
2600: 3.33827
2750: 3.33560
2800: 3.33513
2875: 3.33472
3000: 3.33457
```

Terminal SoftMuon does not rescue it:

```text
2500: 3.34114
2600: 3.33829
2800: 3.33513
2875: 3.33472
3000: 3.33453
```

LocoProp re-on from 2500, with no gate and an explicit 0.05x base-step norm,
also does not rescue it:

```text
normal:
2525: 3.34036
2550: 3.33962
2575: 3.33891
2600: 3.33829

softpolar:
2525: 3.34037
2550: 3.33963
2575: 3.33892
2600: 3.33830
```

The important diagnostic is that the correction is not being discarded:

```text
normal eff_frac_med:    0.05 at 2500, 2525, 2550, 2575
softpolar eff_frac_med: 0.05 at 2500, 2525, 2550, 2575
```

The local objective is also not failing. In the tail re-on probes, K5 improves
the local matching objective in all 12 logged MLP-fc layers:

```text
normal K5 loss/loss0:    roughly 0.914-0.924
softpolar K5 loss/loss0: roughly 0.911-0.919
good loss layers:        12 / 12
```

So the failure is not:

```text
not enough accepted layers
not enough local descent
not enough applied correction norm
not enough softpolar shaping
```

## Direction Budget

The problem is direction and target semantics.

At 2500 with normal 0.05x LocoProp:

```text
eff/base med: 0.0500
cos med:      0.0075-0.0095
aligned frac: 0.000375-0.000475
```

That means a 5 percent correction contributes only about 0.04-0.05 percent of a
base Muon step in the base-step-aligned direction.

To contribute even 1 percent aligned, pure scaling would require:

```text
about 21x-27x more LocoProp scale
total correction norm: about 1.05x-1.33x one full Muon step
```

To contribute 5 percent aligned:

```text
total correction norm: about 5.3x-6.7x one full Muon step
```

That is not a sane "just make alpha bigger" regime. It would be a large
sideways perturbation.

## Current Implementation Semantics

The generated implementation currently prepares a local correction before the
base optimizer step:

```python
prepare_locoprop_m(model, step)
for opt in optimizers:
    opt.step()
flush_locoprop_m_apply_stats(step)
```

For MLP-fc, the local target is built from the raw local target:

```python
target = pre0 - gamma * dpre      # pre target
target = post - gamma * dpre      # post target
W starts from W0
corr = W - W0
```

The correction is applied inside the Muon optimizer after the normal update is
already computed and applied:

```python
p.add_(update, alpha=-lr)
_locom_apply_owned_param_(p, update, lr)
```

Therefore the correction is not solving the residual left by Muon. It solves a
raw local target, then adds that raw correction on top of a Muon step that may
already have consumed most of the locally useful target displacement.

This explains the observed combination:

```text
local objective improves;
correction is applied;
cosine with base step is tiny;
validation curve does not move.
```

The local solve can be locally right but globally redundant or sideways with
respect to the already-planned Muon displacement.

## Hypothesis

The LocoProp-M primitive should be a residual correction on top of Muon, not an
independent raw local target solve.

Current additive semantics:

```text
base update:       Delta_muon
LocoProp target:   Q X ~= -gamma dY
applied update:    Delta_muon + alpha Q
```

Residual semantics:

```text
base update:       Delta_muon
residual target:   Q X ~= -gamma dY - Delta_muon X
applied update:    Delta_muon + alpha Q
```

For the MLP-fc pre-space target:

```text
target_pre_residual = pre0 - gamma dpre - (Delta_muon @ x.T).T
```

Equivalently, initialize the local solve at the post-Muon weight:

```text
W_base = W0 + Delta_muon
solve W near W_base against the same local target
corr = W - W_base
apply corr after base update
```

This is the next principled thing to test because it directly addresses why the
current correction has tiny useful projection despite improving the local
objective.

## Cheapest Next Probe

Do not launch another broad schedule sweep. Use the warm pod only for one
mechanism probe.

Start from the existing remote step-2000 or step-2500 checkpoint and test:

```text
surface: MLP-fc
target_space: post, true_post_grad=1
K: 5
inner_lr: 2e-4
sample_tokens: 2048
active window: 2500:2600 first, then 2000:2125 if promising
norm_target: 0.05
gate: off for first measurement
mode: residual-after-Muon
```

Required logging:

```text
base_local_loss: local target loss under W0
muon_local_loss: local target loss under W0 + Delta_muon
residual_lossK:  local target loss after residual solve
raw_target_norm: ||-gamma dpre||
residual_target_norm: ||-gamma dpre - Delta_muon X||
cos(corr_raw, base_step)
cos(corr_residual, base_step)
cos(corr_residual, residual_descent)
applied eff/base
```

Decision gate:

```text
If residual target norm is tiny, Muon already solves the local target and
LocoProp has no independent work to do in this state.

If residual target norm is nontrivial but residual correction remains
near-orthogonal and validation-tied, the local sampled objective is not the
right target.

If residual correction improves 2500->2600 slope versus cold, promote to a
2000->2250 probe.
```

## Current Verdict

LocoProp-M is not disproven as a primitive. The current version is likely
solving the wrong local problem for an additive Muon hybrid.

The key next question is not "K5 or K10" and not "normal or softpolar." It is:

```text
does the local correction solve the residual that Muon leaves behind?
```

Until that is answered, more suffix LR schedules are lower value than the
residual-after-Muon probe.
