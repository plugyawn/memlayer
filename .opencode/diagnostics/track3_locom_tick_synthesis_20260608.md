# Track 3 LocoProp-M Tick Synthesis - 2026-06-08

Scope: what the current local evidence says about making the c_fc
LocoProp-M correction actually matter, with emphasis on short local solves
(`K=5-10`).

## Bottom Line

The current evidence does not say "use more local steps." It says:

```text
true-post local objective + K=5 is already enough to solve the local subproblem
reasonably well.

The missing condition is application scale / trajectory coupling: the local
correction is locally meaningful but globally too small or too late to separate
from alpha-zero controls.
```

So the thing that would make LocoProp-M tick is not raw local optimizer depth.
It is making the local solve produce a meaningful functional displacement while
the base optimizer still has enough LR/state budget to use the changed weights.

## Evidence

### 1. K=5, K=8, and K=10 have the same validation curve

From the 1600 checkpoint, same seed and schedule:

| lane | 1600 | 1625 | 1650 | 1700 | 1800 |
| --- | ---: | ---: | ---: | ---: | ---: |
| K5 lr2e-4 | 3.48241 | 3.45135 | 3.43562 | 3.41883 | 3.39870 |
| K8 lr2e-4 | 3.48241 | 3.45135 | 3.43562 | 3.41884 | 3.39870 |
| K10 lr2e-4 | 3.48241 | 3.45134 | 3.43562 | 3.41884 | 3.39873 |
| no-Loco / alpha-zero | 3.48241 | 3.45136 | 3.43562 | 3.41884 | 3.39874 |

This is the most important negative result. The local correction is present,
but validation is not separating from the control in this screen.

### 2. More K improves local loss but not validation

At step 1600, K10 improves the local objective much more than K5:

```text
K5 median local loss/loss0:  0.904
K8 median local loss/loss0:  0.859
K10 median local loss/loss0: 0.833
```

At step 1700:

```text
K5 median local loss/loss0:  0.908
K8 median local loss/loss0:  0.867
K10 median local loss/loss0: 0.881
```

The K-depth curve says K5 is already on the useful part of the local-solve
curve. K8/K10 are better local solvers, but the global model does not care
under parameter-norm scaling.

### 3. K10 is not strictly safer

K10 can overshoot individual layers even when the median looks fine. At step
1675, layer 11 had:

```text
K4 ratio:   1.566
K5 ratio:   3.728
K8 ratio: 137.4
K10 ratio: 45.51
```

That is a local objective blow-up in one layer. K5 is the safer default unless
we add per-layer rollback or a stricter per-layer local-loss gate.

### 4. Layer behavior is not uniformly bad

Median K5 layer stats over steps 1600-1775:

| layer | median loss/loss0 | median cos | cos>=0 frac | read |
| ---: | ---: | ---: | ---: | --- |
| 0 | 0.996 | +0.030 | 1.00 | almost no local movement |
| 1 | 0.975 | +0.024 | 0.88 | mild |
| 2 | 0.840 | +0.007 | 0.62 | strong local gain, unstable direction |
| 3 | 0.937 | +0.012 | 0.62 | moderate, unstable |
| 4 | 0.954 | +0.013 | 0.75 | mild |
| 5 | 0.946 | +0.013 | 0.88 | mild |
| 6 | 0.922 | +0.011 | 0.88 | moderate |
| 7 | 0.897 | +0.002 | 0.75 | strong local gain, weak descent cosine |
| 8 | 0.875 | +0.004 | 0.75 | strong local gain, weak descent cosine |
| 9 | 0.853 | +0.004 | 0.88 | strong local gain, weak descent cosine |
| 10 | 0.837 | +0.009 | 1.00 | strong local gain |
| 11 | 0.834 | +0.000 | 0.50 | strong local gain, fragile direction |

The pattern is not "every layer is bad." It is:

```text
later MLP layers solve a stronger local problem,
but their global descent alignment is small and noisy.
```

That makes a layer subset plausible, but not because other layers cannot solve.
It is because layer 0/1 barely move and layer 11 can become unstable with too
many local steps.

### 5. True-post target is required

The older K-diagnostic pass already showed the target-space split:

```text
post-approx/preactivation K10: can explode by orders of magnitude
true-post K10: stable, local loss/loss0 below 1.0, bad_loss 0/12
```

So the working primitive is specifically:

```text
TRACK3_LOCOM_TARGET_SPACE=post
TRACK3_LOCOM_TRUE_POST_GRAD=1
```

This is not optional. The preactivation/post-approx variants are different
objects and should not be used to decide whether LocoProp-M works.

### 6. Sample size was not the key

The 2048-token diagnostic reduced some noise, but it did not change the result
or eliminate unstable layers. The run matched the 1024-token validation curve
around 1800:

```text
sample2048: 3.39871 @1800
sample1024: 3.39870 @1800
```

It also still had layer blow-up events in diagnostics. Bigger samples make the
local estimate cleaner, but they do not solve the global-application problem.

### 7. The correction is too small in parameter-scaled mode

Parameter-scaled K10 application at 1600-1775:

```text
base step median:          0.422 -> 0.323
effective correction/base: ~0.01-0.02 median
```

Late residual mode forced a visible `0.05x` base-step correction from 2500,
and still matched the cold/no-Loco tail:

```text
2500: 3.34115
2525: 3.34036
2550: 3.33962
2575: 3.33890
2600: 3.33829
```

So a slightly larger parameter-space norm cap is not enough. The correction
needs to be scaled in activation/function space, or applied earlier.

### 8. Activation scaling is the next real test, but currently incomplete

The act-base path is implemented and committed:

```text
TRACK3_LOCOM_SCALE_MODE=act_base
TRACK3_LOCOM_ACT_TARGET=1.0
TRACK3_LOCOM_NORM_CAP=1.0
```

The first visible run loaded the 1600 checkpoint and produced:

```text
1625: 3.45140
```

That is sane, but it is not yet evidence of a gain because it ties the old
K5/K10 screen. The run was timer-terminated before later artifacts were pulled.

## Current Tick Conditions

These are the conditions supported by evidence:

```text
surface:              MLP c_fc
target:               true-post
local optimizer:      SGD
local steps:          K=5 first, K=8/10 only with per-layer rollback
inner_lr:             2e-4 first
prox:                 0.1
sample_tokens:        1024 enough for screens
gating:               require local loss decrease; cos>=0 is useful but not sufficient
application scale:    activation-relative, not Frobenius-only
timing:               test at 1600-1800/2000, not 2500+
control:              alpha-zero/no-Loco with identical schedule and generated path
```

The "tick" criterion should be strict:

```text
By 1700, active must separate from alpha-zero by more than local eval noise.
By 1800, active must keep or widen that separation.
If it does not, the local correction is not the causal ingredient for that run.
```

## Next Probe Ladder

Do not launch these until Prime auth and budget are sane. If launched, pull logs
before any timer kills the pod.

### Probe A0: delayed onset from a simple-Muon prefix

This tests the "let Muon capture breadth first" hypothesis directly. Run from
step 0, not from the old red/LocoProp 1600 checkpoint:

```text
lane 1: no-Loco/simple-Muon control to 2000
lane 2: simple Muon until 1200, then act_base LocoProp to 2000
lane 3: simple Muon until 1600, then act_base LocoProp to 2000
```

Default runner:

```text
.opencode/prime_scripts/run_prime_track3_delayed_locom_onset.sh
```

Low-budget resume runner:

```text
.opencode/prime_scripts/run_prime_track3_delayed_locom_resume_onset.sh
```

The resume runner is the preferred Prime path while wallet is tight: it trains
the simple-Muon prefix once, saves `1200` and `1600` checkpoints, then resumes
the active LocoProp lanes from those exact prefix states. This preserves
optimizer/RNG/data-stream provenance while avoiding duplicate prefix compute.
Default `TRACK3_TRAIN_STEPS=1800` is the cheap gate; set it to `2000` after a
refill if `1800` separates.

Default LocoProp settings:

```text
surface=fc
K=5
inner_lr=2e-4
prox=0.1
target=true-post
scale_mode=act_base
act_target=0.50
norm_cap=1.0
```

Gate:

```text
start1200 must beat control by 1500/1600 and keep the gap to 1800/2000.
start1600 must beat control by 1700/1800 and keep the gap to 2000.
```

If this fails, then "Muon breadth first" alone is not enough; the LocoProp
correction either needs a different surface or is not the causal source of the
prefix descent.

### Probe A: activation-scale ladder to 1800

Same checkpoint and schedule, three lanes:

```text
act_base target 0.25
act_base target 0.50
act_base target 1.00
```

Use:

```text
K=5
inner_lr=2e-4
prox=0.1
norm_cap=1.0
active=1600:1800
diag every 25
alpha-zero paired control
```

Gate:

```text
active must beat alpha-zero by 1700 and 1800.
```

If none separate, the c_fc LocoProp correction is not currently driving the
prefix win.

### Probe B: layer subset only if A separates

If activation scaling works, test:

```text
layers 2,6,7,8,9,10
layers 7,8,9,10
all layers
```

Rationale: layers 7-10 have large local gains; layer 2 has strong local gain
but noisier direction; layer 11 is fragile under larger K; layers 0-1 are
mostly too small to matter.

### Probe C: K-depth only after scale works

If act-base K5 separates, then compare:

```text
K=5
K=8
K=10 with per-layer rollback
```

Without activation-scale separation, extra K is wasted compute.

## Practical Read

LocoProp-M "ticks" locally already. It lowers a clean local objective in nearly
every MLP layer. It has not yet "ticked" globally under the current parameter
norm cap, because the applied displacement is too small or too orthogonal to
the descent needed by the global model.

The most plausible remaining way to make it matter is MuP-style activation
scaling during the 1600-2000 window. The act-base implementation is the right
probe, but the first run was incomplete and must be repeated with an explicit
alpha-zero control and artifact pull.
