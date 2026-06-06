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

## True-Post Scale Ladder - 2026-06-06

Artifact directory:

```text
.opencode/current_track3_ledger_20260606_logs/kdiag_scale_035786/
```

Profiles:

```text
post-true-k10-lr1e4-alpha0
post-true-k10-lr2e4-alpha0
post-true-k10-lr3e4-alpha0
post-true-k10-lr1e3-alpha0
```

K=10 summary:

```text
inner_lr=1e-4:
  median loss/loss0 9.044e-01, corr_norm 4.069e-03,
  bad_loss 0/12, nonfinite 0, pos-cos 8/12

inner_lr=2e-4:
  median loss/loss0 8.327e-01, corr_norm 6.757e-03,
  bad_loss 0/12, nonfinite 0, pos-cos 9/12

inner_lr=3e-4:
  median loss/loss0 8.297e-01, corr_norm 9.128e-03,
  bad_loss 1/12, nonfinite 0, pos-cos 9/12

inner_lr=1e-3:
  median loss/loss0 7.789e-01, corr_norm 2.842e-02,
  bad_loss 3/12, nonfinite 0, pos-cos 11/12
```

Read:

- The true-post local solve is not dead. Scaled correctly, it reduces the local
  objective by `~10-17%` median without nonfinite corrections.
- `2e-4` is the clean active candidate: useful local reduction, correction norm
  inside the desired `1e-3..1e-2` band, and no bad-loss layers.
- `3e-4` is the edge of the clean region. It is similar median local reduction
  but already has one bad-loss layer.
- `1e-3` is too hot for all-layer active use. It reduces median local loss more,
  but correction norm is above the target band and bad-loss layers rise to
  `3/12`; use it only for layer-restricted or stronger-gated tests.

Active screen launched from the same pod:

```text
track3_kdiag_post-true-k10-lr2e4-active-poscos_095921
```

Settings:

```text
K=10
inner_lr=2e-4
true_post_grad=1
require_loss_decrease=1
min_cos_desc=0.0
train_steps=1800
```

Result:

```text
1600: 3.48241
1625: 3.45139
1650: 3.43530
1675: 3.42536
1700: 3.41809
1725: 3.41258
1750: 3.40855
1775: 3.40573
1800: 3.40452
```

Read:

- The active `2e-4` true-post local solve beat the previously useful
  `B1 softmerge1600` reference by `0.01689` at `1800` and `0.02490` at `1750`.
- It beat the weak `3.46252 @1800` family by `0.05800`.
- Applied corrections were not cap-limited (`scale=1.000e+00` on logged applied
  layers), so this is evidence for a real local-solve update rather than another
  capped perturbation.

## True-Post Active 3000-Schedule Check - 2026-06-06

Artifact directory:

```text
.opencode/current_track3_ledger_20260606_logs/truepost3000_848672/
```

Run:

```text
track3_truepost3000_post-true-k10-lr2e4-active-poscos_103924
```

Settings:

```text
K=10
inner_lr=2e-4
true_post_grad=1
require_loss_decrease=1
min_cos_desc=0.0
train_steps=3000
active_windows=0:3000
```

Result:

```text
1600: 3.48241
1625: 3.49295
1650: 3.49193
```

Comparison:

```text
short 1800 active screen:
1625: 3.45139
1650: 3.43530
1800: 3.40452

proper 3000 active screen:
1625: 3.49295
1650: 3.49193
```

Read:

- This is a negative result for naive extension to the full 3000 schedule.
- The correction did not become unsafe: logged applied corrections were
  uncapped (`scale=1.000e+00`) and remained around `1e-3..2e-2`.
- The difference is relative scale. In the 3000 schedule, the logged `c_fc`
  base Muon step was about `1.29` at `1600` and `1.27` at `1625`, so the same
  true-post correction is much too small to move the trajectory.
- Therefore, "what makes LocoProp tick" currently includes the schedule/relative
  scale: the true-post local solve is locally sane, but it only moves validation
  when its magnitude is a meaningful fraction of the active Muon update.

Apply-scale summary, generated with
`tools/analyze_locom_apply_scale.py`:

```text
short 1800 active screen:
step  base_med  eff_frac_med  eff_frac_p90
1600  0.3080    0.02636       0.06374
1625  0.2694    0.02115       0.05442
1750  0.0770    0.05339       0.14470

proper 3000 active screen:
step  base_med  eff_frac_med  eff_frac_p90
1600  1.2930    0.006276      0.01517
1625  1.2700    0.004056      0.01454
```

So the successful screen lives in the `~0.02-0.05` median correction/base-step
band, while the failed 3000 run was closer to `~0.004-0.006`.

Updated rule:

- Do not repeat all-layer `inner_lr=2e-4` true-post active under a hot 3000
  schedule without relative normalization.
- The next credible test should set a correction target as a fraction of the
  base Muon step, or run a colder/local window where the correction naturally
  occupies that fraction.
- Two explicit next profiles now exist:

```text
post-true-k10-lr2e4-active-poscos-norm002
  TRACK3_LOCOM_NORM_TARGET=0.02

post-true-k10-lr2e4-active-poscos-norm005
  TRACK3_LOCOM_NORM_TARGET=0.05
```

These preserve the locally sane true-post `K=10`, `inner_lr=2e-4` direction and
only change the relative size of the state-decoupled correction.

## 2026-06-06 SXM warm-pod norm-target check

Pod: `c57f71bf40964f2ab874120ddd3140cd`, H100 80GB SXM5.

The norm-target hypothesis was tested on the same pod/checkpoint/code path:

```text
checkpoint: track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt
K=10
inner_lr=2e-4
true_post_grad=1
require_loss_decrease=1
min_cos_desc=0.0
```

Results at the first post-resume validation:

```text
3000 schedule, norm_target=0.02: 3.49340 @1625
3000 schedule, norm_target=0.05: 3.49298 @1625
1800 short schedule control:     3.45139 @1625
```

The 1800 short-schedule control completed on the same SXM pod:

```text
1600: 3.48241
1625: 3.45139
1650: 3.43530
1675: 3.42535
1700: 3.41808
1725: 3.41258
1750: 3.40855
1775: 3.40573
1800: 3.40453
```

Read:

- The short-screen LocoProp hit reproduced exactly on the SXM pod.
- Forcing the same local correction to `2%` or `5%` of the Muon base step did
  not recover the hit under the hot 3000-step schedule.
- Therefore the effect is not just "make the correction a certain fraction of
  the current Muon update". The schedule/temperature changes the actual
  training dynamics: by step 1600 the 1800 schedule has a much smaller logged
  base Muon step (`~0.308` at 1600, `~0.269` at 1625), while the 3000 schedule
  is still around `~1.29`/`~1.27`.
- Next credible test should change the schedule/base-update temperature while
  preserving the true-post K10 primitive, rather than increasing the LocoProp
  norm target again.

Launched next:

```text
label=track3_kdiag_post-true-k10-lr2e4-active-poscos-coldp2_115017
TRACK3_TRAIN_STEPS=3000
TRACK3_COOLDOWN_FRAC=1.0
TRACK3_LR_SCHEDULE=power
TRACK3_LR_POWER=2.0
TRACK3_LOCOM_NORM_TARGET=0.0
TRACK3_LOCOM_ACTIVE_WINDOWS=0:3000
TRACK3_LOCOM_END_STEP=3000
```

This tests whether making the base Muon update cold enough, instead of scaling
the LocoProp correction up, is the actual ingredient behind the short-screen
gain.

First coldp2 gate:

```text
1600: 3.48241
1625: 3.45135
1650: 3.43562
1675: 3.42613
1700: 3.41883
1725: 3.41289
1750: 3.40792
1775: 3.40359
1800: 3.39872
1825: 3.39518
1850: 3.39175
1875: 3.38819
1900: 3.38477
1925: 3.38173
1950: 3.37909
1975: 3.37605
2000: 3.37337
2025: 3.37101
2050: 3.36869
2075: 3.36658
2100: 3.36425
2125: 3.36217
2150: 3.36005
```

This matches the 1800 short-schedule control at the first gate (`3.45139`) while
remaining a 3000-step run. The logged base step is intermediate:

```text
hot 3000 base_step @1600/1625:    ~1.29 / ~1.27
short 1800 base_step @1600/1625:  ~0.31 / ~0.27
coldp2 3000 base_step @1600/1625: ~0.42 / ~0.41
```

So the live hypothesis is now schedule/base-update temperature, not simply
LocoProp correction/base normalization.

The important change versus the pure 1800 control is after the old endpoint:
the 1800 run ended at `3.40453`, while coldp2 is already `3.39872 @1800` and
continues descending. This suggests the useful lever is not "end the run at the
cold point", but "enter the LocoProp-friendly low-base-step regime while keeping
enough tail LR alive."

By `2000-2075`, the slope has visibly tapered. The run should continue for
evidence, but the next design target is a cold prefix that unlocks the
LocoProp-friendly trajectory followed by a smoother/warmer tail; another
LocoProp norm-target increase is no longer the obvious lever.

By `2125-2150`, it is still descending but with little margin:
`3.36217 @2125`, `3.36005 @2150`. The trajectory needs roughly `0.0021-0.0023`
per 25 steps from here to reach 3.28 by 3000, so any further taper misses.

By `2400`, the run is still LocoProp-active and still using the same 1024-token
sample path:

```text
2175: 3.35803
2200: 3.35629
2225: 3.35478
2250: 3.35306
2275: 3.35149
2300: 3.34996
2325: 3.34865
2350: 3.34747
2375: 3.34629
2400: 3.34514
```

`locoprop_m_prepare step=2400` still reports local loss decrease and positive
cosine for 3/4 logged layers. The logged application path also still runs, but
the base Muon step has fallen to about `7.76e-02`. This rules out the simple
explanation that the late taper is caused by accidentally stopping LocoProp at
1800. The better read is:

- a cold base update makes the LocoProp prefix viable;
- too much coldness later starves the tail even while LocoProp remains on;
- the next useful diagnostic is a cold prefix plus smoother/warmer tail, not a
  bigger LocoProp correction or another 1024-vs-2048 sample-token check.
