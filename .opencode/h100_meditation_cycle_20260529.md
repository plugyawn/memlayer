# H100 / Meditation Cycle Log - 2026-05-29

All times are local IST unless noted.

## Cycle A

```text
GPU block observed: carried over from 2026-05-28 UTC run logs into 2026-05-29 session context.
Local audit time: 2026-05-29 20:54 IST.
Modal active apps after block: none.
```

H100 work completed:

```text
ap-o5TWf9hEoWqS8Y93OYsdh9
  v_postvarred_pulse64_b002_rep2_h100_20260528
  result: finite 48-64 V pulse failed replication.

ap-V8Y0hd73A1CbvY4oDCL3KF
  v_postvarred_finite_t_b002_h100_20260528
  result: finite-t sweep did not beat matched no-op.
```

Meditation block started:

```text
2026-05-29 20:54 IST
```

Analysis focus for this block:

```text
1. Audit schedule-only/no-op path semantics.
2. Explain why active V metric produces early movement but loses by 200.
3. Decide whether the next allowed H100 hour should test path controls, post-window state, or be skipped.
```

Findings:

```text
2026-05-29 21:02 IST

schedule_only is effectively a pure baseline control in the post-varred V
suite: stats are disabled, preconditioner application is skipped, and the update
falls through the same fused polar/variance-reduction path as baseline.

The apparent schedule_only wins are therefore not meaningful optimizer alpha.
The suite was missing a fixed run seed, so each case likely used a different
random initialization. That contaminates baseline/no-op/active comparisons.

Patch prepared:
  - TRAIN_RUN_SEED support in train_gpt.py.
  - run_newtonv_experiment_suite.sh now sets TRAIN_RUN_SEED=1337 for all cases.

Next H100 hour should start with a small seeded control sanity check before any
new algorithmic sweep.
```

Prepared next H100-hour suite:

```text
NEWTONV_SUITE=v_seed_sanity
default seed: NEWTONV_RUN_SEED=1337
cases:
  vss_baseline_a
  vss_baseline_b
  vss_schedule_only_postvarred_r020_blend002
  vss_noop_postvarred_r020_blend002
  vss_finite_t20_postvarred_r020_blend002

Expected control result:
  baseline_a == baseline_b == schedule_only at printed validation precision.
  no-op should also match if blend=0 is truly update-identical.

If this fails:
  stop interpreting the old active/no-op deltas and fix determinism/control
  semantics first.
```

Seed sanity H100 completed:

```text
App: ap-mGqPxnv2ZneOpnHCr7oQOu
Label: v_seed_sanity_h100_20260530
Seed: TRAIN_RUN_SEED=1337
```

Results:

```text
vss_baseline_a:                            4.1864, 570.55ms/step
vss_baseline_b:                            4.1816, 564.52ms/step
vss_schedule_only_postvarred_r020_blend002 4.1818, 563.02ms/step
vss_noop_postvarred_r020_blend002          4.1856, 572.34ms/step
vss_finite_t20_postvarred_r020_blend002    4.1839, 568.87ms/step
```

Conclusion:

```text
The sanity check failed its intended strict criterion. baseline_a and
baseline_b did not match at printed precision despite the same seed, and the
spread is too large for the small endpoint deltas we were trying to interpret.

Do not launch more surface sweeps until the harness can compare active and
control paths from an identical saved state or enough paired reps are budgeted.
The next implementation task should be an exact-state paired harness, not a new
Newton-V variant.
```

## Cycle B

```text
Start: 2026-05-30 03:25 IST
GPU apps:
  ap-sIPAlW5pW8d8jh8WmQauyL stopped early after harness bug discovery.
  ap-ErqIbqU8hOiOizylwu7Gcn completed repaired paired sanity.
Modal active NanoGPT apps after block: none.
```

Implementation work:

```text
811cf32 Add paired NewtonV replay harness
5acb4f4 Clone optimizer anchor for paired replay
```

H100 result:

```text
paired_noop:   s40=5.5987  s80=4.5217
paired_active: s40=5.6120  s80=4.5279
paired_noop2:  s40=5.6035  s80=4.5300
```

Conclusion:

```text
The exact-state paired harness is now the right default for small optimizer
deltas. The current V finite-t post-varred pulse did not beat paired controls.

Next meditation focus:
  1. Whether the remaining no-op/noop2 spread is acceptable or needs repeated
     paired no-op calibration.
  2. How to implement the V post-window optimizer-state tail ablation.
  3. Whether MLP c_fc activation-metric polar is the next cleaner theory probe.
```

Prepared next non-launched suite:

```text
Commit: 4e8d4ff Add paired MLP fc metric suite
Suite: NEWTONV_SUITE=mlpfc_paired_metric
Default cases: noop,active,noop2
Default surface: mlp_fc
Default mode: activation-metric polar
Default layers/window: layers 0-1, collect 0-112, apply 48-112
```

Rationale:

```text
V finite-t post-varred is not currently a hit under paired controls. The next
cleaner theory probe is c_fc because it is an affine 768-dimensional surface
where right-side feature geometry should map most directly to KFAC/LocoProp /
Newton-Muon reasoning. The paired harness should be used before any broad
QKVO sweep.
```

## Cycle C

```text
Start: 2026-05-30 11:16 IST
GPU apps:
  ap-xqRQZMenCXKMs6lphHEQbT completed additive V paired probe.
  ap-FyYEObCFk1Z3R8eX5SxFOA completed additive MLP c_fc paired probe.
Modal active NanoGPT apps after block: none.
```

Implementation work:

```text
17bdaf9 Add additive LocoProp correction path
```

H100 results:

```text
V layers 0-1 additive finite_t=2 norm-to-base:
  paired_noop:   s80=4.5281
  paired_active: s80=4.5242
  paired_noop2:  s80=4.5316

MLP c_fc layers 0-1 additive finite_t=2 norm-to-base:
  paired_noop:   s80=4.5330
  paired_active: s80=4.5259
  paired_noop2:  s80=4.5282
```

Conclusion:

```text
The additive/state-decoupled LocoProp translation is now the hot path. It is
not conclusive, but it is the first paired pattern where active beats both
controls on two different 768-dimensional surfaces.

This says the right feature axis probably should not be inserted into Muon
momentum/polar state. Treat it as a local correction on top of an otherwise
unchanged NorMuon update.

Immediate next work:
  1. Add correction/base norm logging.
  2. Rerun V and c_fc with raw additive scaling versus norm-to-base.
  3. Extend the best additive variant to 120/200 if it still clears controls.
  4. Measure incremental additive overhead against a matched schedule-only
     control rather than reading the normal late-screen 650ms segment as
     additive-specific overhead.
```

## Cycle D

```text
Start: 2026-05-30 16:39 IST
GPU apps:
  ap-yzeLUb0oYbyBN9kTQvg5Wv completed additive V 120-step paired probe.
Modal active NanoGPT apps after block: none.
```

H100 result:

```text
V layers 0-1 additive finite_t=2 norm-to-base, collect 0-64, apply 48-64:
  paired_noop:   s80=4.6204  s120=4.1849  step_avg=450.34ms
  paired_active: s80=4.6230  s120=4.1840  step_avg=449.87ms
  paired_noop2:  s80=4.6201  s120=4.1821  step_avg=448.44ms
```

Conclusion:

```text
The V additive 80-step hit did not persist cleanly at 120.

Active is not slower than the controls, and the first-noop compile stall was
fixed by the expanded warmup list. But active is worse than both no-ops at
step 80 and loses to noop2 at step 120. This is within the paired control
floor, not a promotion result.

Next meditation focus:
  1. Check whether c_fc additive survives 120; it was the other positive
     80-step surface and is theoretically cleaner.
  2. If c_fc fades too, stop broad surfaces and tune additive scale from the
     logged correction/base ratios.
  3. Keep V additive demoted until a different scale/window/filter clears a
     paired persistence run.
```

## Cycle E

```text
Start: 2026-05-30 16:50 IST
GPU apps:
  ap-KVxwzxzDJLLJZaMrvrMiRh completed additive MLP c_fc 120-step paired probe.
Modal active NanoGPT apps after block: none.
```

H100 result:

```text
MLP c_fc layers 0-1 additive finite_t=2 norm-to-base, collect 0-64, apply 48-64:
  paired_noop:   s80=4.6216  s120=4.1816  step_avg=450.25ms
  paired_active: s80=4.6302  s120=4.1871  step_avg=450.59ms
  paired_noop2:  s80=4.6215  s120=4.1865  step_avg=449.88ms
```

Conclusion:

```text
c_fc additive also failed the 120-step persistence check.

This is a cleaner negative than V: active is worse at step 80 by a visible
margin and does not recover by step 120. The run is timing-matched, so this is
not a wall-clock or compile artifact.

Next meditation focus:
  1. Do not spend the next H100 slot on more surfaces with this same finite_t=2
     norm-to-base pulse.
  2. Enable additive correction/base diagnostics in the paired suite.
  3. Use a short logging run to decide whether raw additive alpha should be
     much smaller, whether the window should be earlier/shorter, or whether
     finite_t=2 is simply too strong.
```

## Cycle F

```text
Start: 2026-05-30 16:59 IST
GPU apps:
  ap-iIhHsJzH6OrAZtx2YZ7JDV failed during warmup due SCREEN_STEPS=80 warmup
  bounds including steps 80/81.
  ap-IiMgJfVFpD8khiDOCjBTeQ completed fixed combined diagnostic active-only.
  ap-zNbutS7o17tfwdxzyBUaga completed combined 80-step paired probe.
  ap-lvEWc3bzcodHQ5swpTS5zf completed combined 120-step paired probe.
  ap-RzBJfiUbhrh2IoOq98oNtK completed combined 120-step longer-window probe.
Modal active NanoGPT apps after block: none.
```

Implementation work:

```text
4c0144a Allow additive paired combined surfaces
00e9ff4 Fix additive diagnostic parsing and warmup bounds
```

H100 results:

```text
Combined V + MLP c_fc, layers 0-1, finite_t=2, ridge=0.20, norm-to-base.

80-step paired, apply 48-64:
  paired_noop:   4.5353
  paired_active: 4.5267
  paired_noop2:  4.5375

120-step paired, apply 48-64:
  paired_noop:   s80=4.6282  s120=4.1851
  paired_active: s80=4.6159  s120=4.1841
  paired_noop2:  s80=4.6192  s120=4.1858

120-step paired, apply 48-80:
  paired_noop:   s80=4.6268  s120=4.1868
  paired_active: s80=4.6233  s120=4.1851
  paired_noop2:  s80=4.6293  s120=4.1875
```

Diagnostics:

```text
At measured active steps, raw additive correction norm is huge:
  c_fc: 14x-27x base update
  V:     6x-18x base update

Norm-to-base correction is directionally nontrivial:
  c_fc cosine to base update: about 0.34-0.43
  V cosine to base update:    about 0.17-0.21
```

Conclusion:

```text
The single-surface additive results failed at 120, but the combined V+c_fc
surface is not dead. It produces a clear 80-step paired win and a tiny 120-step
residue. That is consistent with a real early pulse whose scale/window is not
yet right.

The longer 48-80 application window was worse than the shorter 48-64 pulse at
step 80 and did not create a stronger endpoint. Therefore the next experiment
should reduce alpha rather than keep the correction active longer.

Queued next:
  blend_max=0.025, same combined V+c_fc 48-64 pulse, 120-step paired.
```

## Cycle G

```text
Start: 2026-05-30 17:37 IST
GPU app:
  ap-8eOdEIkaAbx45x4Xil0umd completed low-alpha combined V+c_fc probe.
Modal active NanoGPT apps after block: none.
```

H100 result:

```text
Combined V + MLP c_fc, layers 0-1, finite_t=2, ridge=0.20, norm-to-base.
Apply window: 48-64
Blend max: 0.025

paired_noop:   s80=4.6171  s120=4.1834  step_avg=448.99ms
paired_active: s80=4.6156  s120=4.1829  step_avg=448.83ms
paired_noop2:  s80=4.6162  s120=4.1810  step_avg=450.63ms
```

Conclusion:

```text
Lower alpha does not promote. Active is only slightly better than the first
noop and worse than noop2 at both measured checkpoints. The alpha=0.05 run had
a bigger step-80 signal; alpha=0.025 mostly erased it.

This means the immediate issue is probably not simple over-application of the
same norm-to-base finite_t correction. The next GPU slot should not be spent
on another scalar tweak of this exact object.

Meditation target before next launch:
  1. Decide whether to test raw additive with alpha derived from the 6x-27x
     norm-ratio diagnostics.
  2. Decide whether to implement activation-metric local correction
     polar(G L^-T) L^-1 rather than finite_t inverse.
  3. Decide whether surface pairing should move from V+c_fc to V+O or QK+V.
  4. If staying with norm-to-base, test shorter pulse timing, not smaller
     alpha.
```

## Cycle H Plan

```text
Start: 2026-05-30 21:56 IST
GPU state before launch:
  No active NanoGPT Modal app.
```

Meditation result:

```text
The next run should not continue scalar tweaking of the additive finite_t
feature-metric correction. The more basic question is whether hard Polar
Express/Muon is erasing too much singular-value information.

Implemented a non-metric soft-polar probe:
  T_alpha,eps(M) = M (M.T M + eps I)^(-alpha/2)

This applies only to MLP c_fc matrices and leaves c_proj plus attention banks
on baseline NorMuon. It is intentionally isolated from LOCO_DIAG and LOCO_FULL
so a hit or miss is interpretable.
```

Queued H100 test:

```text
NEWTONV_SUITE=softpolar_paired
SP_STEPS=80
SP_VAL_EVERY=40
SP_LAYERS=0-1
SP_WINDOWS=48-64
SP_ALPHA=0.5
SP_EPS=6e-5
SP_BLEND_MAX=1.0
SP_BLEND_STEPS=16
SP_NORM_RESTORE=1
SP_LOG_PRECOND=1
SP_PAIRED_CASES=noop,active,noop2
```

Abort note:

```text
First launch ap-4RQOjj4ZOJtIMwkp1fkZ3T was stopped as invalid.

Reason:
  paired_noop still emitted soft_mlp_fc diagnostics and applied nonzero blend
  in the 48-64 window. The runtime no-op bit was being set on TrainingManager,
  while NorMuonAndAdam.set_loco_step reads optimizer._loco_full_runtime_noop.

Observed before stop:
  paired_noop step 50: blend=0.125, cos to hard polar ~0.996
  paired_noop step 64: blend=1.0, cos to hard polar ~0.77
  paired_noop step 80 val_loss=4.5345, but this was active soft-polar,
  not a control.

Fix:
  run_training_case now propagates runtime_loco_full_noop to
  training_manager.optimizer._loco_full_runtime_noop and clears it after
  each paired case.
```

Fixed H100 result:

```text
App: ap-GkKIN2ulkB1agUh7vWvYCz
Log: .opencode/modal_softpolar_mlpfc_a05_eps6e5_80_paired_h100_20260530.launch.log
Parsed: .opencode/modal_softpolar_mlpfc_a05_eps6e5_80_paired_h100_20260530.parsed.md
Diagnostics: .opencode/modal_softpolar_mlpfc_a05_eps6e5_80_paired_h100_20260530.diagnostics.md

paired_noop:   s40=5.6096  s80=4.5288  step_avg=447.42ms
paired_active: s40=5.6069  s80=4.5420  step_avg=454.57ms
paired_noop2:  s40=5.6024  s80=4.5226  step_avg=446.22ms
```

Decision:

```text
No promotion.

The soft-polar perturbation was active and large enough to matter:
  step 64 target_delta=0.7253, target_cos=0.7370

But it hurt final step-80 loss by:
  +0.0132 vs noop
  +0.0194 vs noop2

This rules out the simple non-metric "hard polar is too aggressive for MLP c_fc
0-1" probe. Same-family alpha sweeps are not the highest-value next GPU use.
```

## Cycle I Fixed-Control Additive Recheck

Reason:

```text
The runtime no-op propagation bug makes prior NEWTONV_PAIRED_CASES controls
suspect. Re-ran the strongest prior additive candidate after the fix.
```

Run:

```text
App: ap-W7ej1upyZmocEhNlgwg0iy
Surface: V + MLP c_fc layers 0-1
Collect 0-64, apply 48-64
finite_t=2.0, ridge_rel=0.20, blend_max=0.05
norm_to_base=1
steps=80
```

Result:

```text
paired_noop:   s40=5.6010  s80=4.5289  step_avg=442.44ms
paired_active: s40=5.6023  s80=4.5329  step_avg=442.37ms
paired_noop2:  s40=5.5944  s80=4.5296  step_avg=442.78ms
```

Conclusion:

```text
No promotion. The prior additive combined-surface hit does not survive true
controls.

The diagnostic pattern is useful:
  norm-to-base update remains very close to baseline direction
  raw local-solve scale is 12x-20x baseline at step64

So this exact normalized additive expression is too weak/geometrically aligned,
while the raw expression is too large without much smaller alpha or a better
spectral trust rule.
```

Next implementation:

```text
Metric-soft Cholesky path is prepared for the next screen:
  Q = T_alpha(G L^-T) L^-1

This is the activation-metric update family between raw metric direction and
hard metric-polar. It reuses the existing full-C Cholesky state.

First queued candidate if GPU is used:
  NEWTONV_SUITE=metricsoft_paired
  MS_SURFACE=v
  MS_LAYERS=0-1
  MS_COLLECT_WINDOWS=0-64
  MS_WINDOWS=48-64
  MS_ALPHA=0.5
  MS_EPS=6e-5
  MS_RIDGE_REL=0.20
  MS_BLEND_MAX=0.02
  MS_NORM_RESTORE=0
```

Metric-soft result:

```text
App: ap-JevPvdAPqSRcioMbnMAsmf

paired_noop:   s40=5.6158  s80=4.5364
paired_active: s40=5.6162  s80=4.5324
paired_noop2:  s40=5.5952  s80=4.5205
```

Interpretation:

```text
No promotion. Active is between controls.

The important diagnostic is scale:
  target_delta at step64 ~= 0.86
  applied_delta at step64 ~= 0.017

The metric-soft target changes the direction, but blend=0.02 almost completely
turns it back into baseline. A follow-up, if run, should use a larger blend
such as 0.10 while keeping the same object.
```

Metric-soft stronger blend result:

```text
App: ap-uRi6CcXKDDbFmhEaYH8685

MS_BLEND_MAX=0.10, otherwise same setup:
  paired_noop:   s40=5.6157  s80=4.5287
  paired_active: s40=5.6090  s80=4.5254
  paired_noop2:  s40=5.5854  s80=4.5188
```

Conclusion:

```text
No promotion. Active is again between controls.

At step64:
  target_delta=0.8677
  applied_delta=0.0868
  applied cos ~= 0.9999

The target is different, but the linear blend still makes the applied update
almost baseline-collinear. Do not keep increasing V-only blend blindly.
```
