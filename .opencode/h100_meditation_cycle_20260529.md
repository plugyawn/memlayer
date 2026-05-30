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
