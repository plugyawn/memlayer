# Track 3 LocoProp-M K-Ladder Plan - 2026-06-06

Goal: stop guessing whether LocoProp-M "works" and measure the local solve
itself over a small K ladder, especially `K=5-10`.

## Current Read

The working long-run primitive is not clean LocoProp-S/M. It is a capped,
state-decoupled MLP `c_fc` perturbation added on top of simple Muon.

Known evidence:

- 500-step screens improved materially versus alpha-zero controls.
- Parsed 500-step logs showed cap-saturated corrections and large
  `lossK/loss0` values, so the local solve itself was often bad.
- The 2048-token sample probe cleaned up some early local diagnostics but did
  not visibly improve loss through `1800`.
- Layer-local failures persist:
  - `sample_tokens=2048`, step `1750`, layer 3:
    `lossK=6.691e+00`, `corr_norm=1.540e+02`, `cos_desc=0.810`.
  - This means the cap is still the safety mechanism.

Two implementation facts matter for interpretation:

1. The default `target_space=post` path treats `relu(pre)^2` features as a
   local linear output. That preserves the first-step matching intuition, but
   it is not the true gradient of the stated local nonlinear loss.
2. The old log's `lossK` was measured before the final local update. The
   generator now recomputes the final local loss after K updates for diagnostics
   and loss-decrease gating.

## New Instrumentation

Files:

```text
tools/make_track3_locoprop_m.py
tools/run_track3_locom_kdiag_probe.sh
tools/analyze_locom_kdiag.py
```

New generator knobs:

```text
TRACK3_LOCOM_DIAG_STEPS=1,2,4,5,8,10
TRACK3_LOCOM_DIAG_MAX_LAYERS=12
TRACK3_LOCOM_TRUE_POST_GRAD=0|1
```

When `TRACK3_LOCOM_DIAG_STEPS` is set, logs include rows like:

```text
locoprop_m_kdiag step=1600 l3 k1:loss=...,ratio=...,corr_norm=...,raw_cos=...,cos=... | k2:...
```

Then summarize with:

```bash
python3 tools/analyze_locom_kdiag.py /root/prime_track3_logs/<label>.log
```

## What Would Make LocoProp Tick

LocoProp-M is worth further tuning if one of these becomes true:

1. **Local solve quality improves with K.**
   - Median `loss/loss0` should decrease from `k1 -> k5/k10`.
   - Bad-loss layers should fall, not rise.
   - Correction norm should not explode by orders of magnitude.

2. **Direction becomes structured rather than cap-random.**
   - Median `cos_desc` does not need to be large, but should not flip negative
     across many layers.
   - `corr_norm` should be comparable enough that a `0.20 * base_step` cap is a
     scale limiter, not a total rescue mechanism.

3. **A profile that is locally sane still moves external validation.**
   - If `pre` or true-post-gradient is locally sane but loses the external
     prefix, the previous win is probably a bounded perturbation/regularizer,
     not a local-solve win.
   - If locally sane and externally positive, then we finally have a real
     LocoProp tuning surface.

## Probe Order

All probes start from:

```text
track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt
```

Run on a prepared H100 pod:

```bash
bash tools/run_track3_locom_kdiag_probe.sh
```

Profiles:

### 1. `post-approx-k10-alpha0`

```bash
TRACK3_KDIAG_PROFILE=post-approx-k10-alpha0 \
bash tools/run_track3_locom_kdiag_probe.sh
```

Purpose: measure the current approximation across `K=1,2,4,5,8,10` without
changing weights (`alpha=0`).

Decision:

- If `k5/k10` generally improves `loss/loss0` and avoids norm blowups, try an
  active fixed-time K10 run.
- If it keeps exploding, more K is not the answer under the current local model.

### 2. `pre-k10-alpha0`

```bash
TRACK3_KDIAG_PROFILE=pre-k10-alpha0 \
bash tools/run_track3_locom_kdiag_probe.sh
```

Purpose: test the convex preactivation local objective where the gradient and
logged local loss are consistent.

Decision:

- If this is sane while post-approx is not, the current post-feature local
  model is the failure point.
- If this is also bad, the sampled target/gradient scale is the failure point.

### 3. `post-true-k10-alpha0`

```bash
TRACK3_KDIAG_PROFILE=post-true-k10-alpha0 \
bash tools/run_track3_locom_kdiag_probe.sh
```

Purpose: test the actual nonlinear `relu(pre)^2` local-loss gradient with a
small default inner LR (`1e-5`).

Decision:

- If true-gradient post is locally stable but tiny, tune inner LR upward.
- If true-gradient post is unstable even at small LR, post-space LocoProp-M is
  not the practical lever here.

### 4. `post-approx-k10-fixedtime-active`

```bash
TRACK3_KDIAG_PROFILE=post-approx-k10-fixedtime-active \
TRACK3_TRAIN_STEPS=1800 \
bash tools/run_track3_locom_kdiag_probe.sh
```

Purpose: active behavior check with the current approximation but fixed total
local time: `K=10, inner_lr=0.04` has the same `K * lr = 0.4` as current
`K=4, inner_lr=0.1`.

Promotion gate:

```text
1750 <= 3.459
1800 <= 3.449
```

This must at least match the old K4 line before spending to 2125.

### 5. `pre-k10-fixedtime-active`

```bash
TRACK3_KDIAG_PROFILE=pre-k10-fixedtime-active \
TRACK3_TRAIN_STEPS=1800 \
bash tools/run_track3_locom_kdiag_probe.sh
```

Purpose: active behavior check for a locally consistent preactivation solve.

Promotion gate: same as above. If it is locally sane but worse externally, it
likely means the useful effect is not a clean LocoProp local solve.

## Kill Rules

- Kill an active K10 profile at `1800` if it is worse than the old K4 line by
  more than `0.0015`.
- Only continue to `2125` if it is tied or better at `1800`, or if local K
  diagnostics are dramatically cleaner and the loss is within noise.
- Do not repeat `sample_tokens=2048` alone. It cleaned up some diagnostics but
  did not move the external curve.

## Current Hypothesis

The useful LocoProp effect is probably:

```text
bounded, layer-correlated perturbation
+ early/cold scheduler interaction
+ simple-Muon state geometry
```

not:

```text
accurate K-step local optimizer converging toward a better local target
```

The K-ladder is designed to either falsify that pessimistic read or identify
the one local-objective variant worth tuning.

## K-Ladder Result - 2026-06-06

Artifact directory:

```text
.opencode/current_track3_ledger_20260606_logs/kdiag_bb96/
```

Computed reports:

```text
combined_summary_v2.md
layer_details_k10_v2.md
gate_report_v2.md
gate_report_v4.md
recommendation_v3.md
recommendation_relaxed_v3.md
recommendation_v4.md
```

The first K-ladder answered the main question for the current implementation:

```text
post-approx current path:
  K=1  median loss/loss0 9.133e-01, corr_norm 3.492e-02, bad_loss 4/12
  K=4  median loss/loss0 2.132e+03, corr_norm 1.030e+00, bad_loss 10/12
  K=10 median loss/loss0 3.128e+04, corr_norm 1.266e+02, bad_loss 8/12

preactivation:
  K=1  median loss/loss0 2.274e+00, corr_norm 7.451e-02, bad_loss 11/12
  K=10 median loss/loss0 6.590e+11, corr_norm 3.918e+04, bad_loss 11/12

true post-gradient:
  K=1  median loss/loss0 9.989e-01, corr_norm 4.724e-05, bad_loss 0/12
  K=10 median loss/loss0 9.890e-01, corr_norm 4.685e-04, bad_loss 0/12
```

The analyzer now parses `inf`/`nan` explicitly. With that correction, the
current post-approx `K=10` row has `4` nonfinite fields in the 12-layer screen,
not merely large finite outliers.

The current automated max-K recommendation is:

```text
post-approx: dead, nonfinite correction, stable layers 1/12
post-true:   scale up true local step, stable layers 12/12,
             median cap multiplier 18.84x
pre:         dead, local loss worsens, stable layers 1/12
```

Layer read:

- Current post-approx at `K=10`: only layer `0` is both locally improved and
  sub-unit correction norm. Layer `1` is near the cliff. Layers `2-11` are not
  usable local solves.
- Preactivation at the old step size is worse. Only layer `0` survives; this is
  not the missing faithful LocoProp form.
- True post-gradient is stable for all layers and monotonically reduces the
  stated local loss, but the correction is tiny.

Scale read for true post-gradient:

At step `1600`, the base Muon `c_fc` step norm is about `4.263e-02`, so the
current `norm_cap=0.20` allows about `8.526e-03` of LocoProp correction norm.
With true post-gradient `K=10, inner_lr=1e-5`, the multiplier needed to hit that
cap ranges from roughly `4.2x` on layer `11` to `94.9x` on layer `0`; the
median is `18.84x`. The current analyzer computes:

```text
lr@corr_min    2.134e-05
lr@corr_max    2.134e-04
lr@median_cap  1.884e-04
```

So `2e-4` is the center of the next meaningful scale probe. `3e-4` is useful
as a just-above-cap stress check, not as the first active default.

## Updated Next Ladder

Do not run active `post-approx K=10` or active `pre K=10`. Those paths are ruled
out by local diagnostics.

The only credible K-ladder continuation is:

```bash
TRACK3_KDIAG_PROFILE=post-true-k10-lr1e4-alpha0 bash tools/run_track3_locom_kdiag_probe.sh
TRACK3_KDIAG_PROFILE=post-true-k10-lr2e4-alpha0 bash tools/run_track3_locom_kdiag_probe.sh
TRACK3_KDIAG_PROFILE=post-true-k10-lr3e4-alpha0 bash tools/run_track3_locom_kdiag_probe.sh
TRACK3_KDIAG_PROFILE=post-true-k10-lr1e3-alpha0 bash tools/run_track3_locom_kdiag_probe.sh
```

Decision gate for the alpha-zero LR sweep:

```text
Promote only if:
  median loss/loss0 remains < 1.0,
  bad_loss is <= 2/12,
  no layer has nonfinite correction,
  median corr_norm is in the 1e-3 to 1e-2 range.
```

If that passes, run exactly one active screen:

```bash
TRACK3_KDIAG_PROFILE=post-true-k10-lr2e4-active-poscos \
TRACK3_TRAIN_STEPS=1800 \
bash tools/run_track3_locom_kdiag_probe.sh
```

This uses true post-gradient, requires local loss decrease, and keeps only
nonnegative-cosine corrections. If it fails by `1800`, the remaining useful
effect is very likely a capped perturbation/scheduler interaction, not a clean
multi-step local optimizer.
