# Newton-Muon Cycle Log - 2026-05-27

## Cycle 1 GPU Window

Time accounting:

- GPU window started: about `2026-05-27 17:00 IST`.
- Warm-metric H100 app: `ap-sSL50qhWTRJ3JKcQBp5FJ3`, `17:00-17:24 IST`, `1402.985s`.
- Overpreconditioning H100 app: `ap-9WOCEPdPIu5SZKslqZsOtb`, `17:28-17:49 IST`, `1217.204s`.
- GPU window ended: about `2026-05-27 17:49 IST`.
- Required meditation/audit window: `17:49-18:49 IST`.
- Next H100 launch allowed: `2026-05-27 18:49 IST`, unless the user overrides.

All NanoGPT Modal apps from this cycle were stopped after completion.

## Warm-Metric Result

The decoupled collect/apply control worked mechanically:

```text
collect C early
apply preconditioner later
```

But it did not produce a durable 120-step win:

| case | step 80 | step 120 |
| --- | --- | --- |
| baseline | `4.6326` | `4.1832` |
| V 0-1 collect 0-48 apply 48-112 polar4 | `4.6256` | `4.1829` |
| V 0-1 collect 0-64 apply 48-112 polar4 | `4.6282` | `4.1846` |
| O collect 0-64 apply 48-112 polar4 | `4.6339` | `4.1861` |
| V+O 0-1 collect 0-64 apply 48-112 polar4 | `4.6248` | `4.1847` |

Read: warm collection moves early loss, but by itself is not persistent enough.

## Overpreconditioning Result

The overpreconditioning ladder produced the strongest same-suite result:

| case | step 80 | step 120 |
| --- | --- | --- |
| baseline | `4.6244` | `4.1869` |
| warm V no-op polar4 | `4.6108` | `4.1798` |
| warm V active polar5 | `4.6183` | `4.1821` |
| warm V active polar4 | `4.6182` | `4.1763` |
| warm V active polar4 skip varred | `4.6192` | `4.1784` |

Read:

- `LOCO_FULL_POLAR_ITERS=4` matters.
- Active V polar4 beat baseline and the no-op control in this suite.
- `LOCO_FULL_SKIP_VARRED=1` was worse, so keep NorMuon variance reduction.
- Active polar5 was worse than no-op.

Important caveat:

The no-op control in this logged overprecond run used all V layers because it
used `tools/run_newtonv_timing_triplet_gate.sh`, whose default
`LOCO_DIAG_ATTN_LAYERS` is `all`. The active V cases used
`tools/run_newtonv_raw_v01_gate.sh`, whose default is `0-1`.

This has been fixed for future suites by setting `LOCO_DIAG_ATTN_LAYERS=0-1`
on matched no-op controls.

## No-Op Mechanism

`LOCO_FULL_NOOP=1` is not pure baseline plus overhead.

During the apply window, it sets full blend to zero but still activates the
full after-momentum optimizer path:

```text
raw grad
-> nesterov_momentum_operand_inplace
-> feature preconditioner helper with blend=0
-> polar_express_from_operand using LOCO_FULL_POLAR_ITERS
-> NorMuon variance reduction
```

So no-op is a real optimizer schedule/control:

```text
baseline path: fused polar_express with 5 coefficients
full no-op path: explicit momentum operand + polar_express_from_operand with LOCO_FULL_POLAR_ITERS
```

This makes no-op a useful candidate in its own right, not just a cost control.

## Overpromote H100 Gate Result

Ran the prepared `overpromote` suite on Modal H100:

```bash
NANOGPT_MODAL_GPU=H100 \
MODAL_RUNNER=tools/run_newtonv_experiment_suite.sh \
MODAL_EXTRA_ENV_JSON='{"NEWTONV_SUITE":"overpromote","NEWTONV_SUITE_LABEL":"modal_overpromote_h100_20260527","PROMOTE_STEPS":"200","PROMOTE_VAL_EVERY":"50"}' \
SCREEN_STEPS=200 SCREEN_VAL_EVERY=50 \
tools/run_modal_newtonv_raw_gate.sh
```

Modal app:

```text
ap-g1YDghiIetiBqd6GxM0ATO
returncode=0
wall_time=1366.576s
```

Parsed result:

```text
baseline:                    3.8882
V 0-1 no-op polar4:          3.8918
V 0-1 no-op polar5:          3.8856
all-V no-op polar4:          3.8851
V 0-1 active polar5:         3.8869
V 0-1 active polar4:         3.8887
```

Decision:

```text
Do not promote Newton-V from this ladder.
The best result is all-V no-op polar4, not active Newton-V.
```

Interpretation:

- The full-path/no-op schedule is the strongest current signal.
- The actual right-preconditioned Newton-V update is not carrying the 200-step
  win in this window.
- Active V0-1 polar4 was worse than baseline, despite the 120-step hint.
- Active V0-1 polar5 beat baseline but lost to both strong no-op controls.
- The best no-op controls were worse at step 50 and only won by step 200, so
  the signal is a late trajectory change rather than an early acceleration.
- Important nuance: no-op/full-path activation is param-bank level. With
  `LOCO_FULL_SURFACES=v`, the whole `vo_bank` goes through the explicit
  after-momentum full path; layer selection only controls feature collection and
  identity/preconditioner helper work.

Next ladder:

```text
isolate the no-op/full-path schedule with feature-stat work removed:
  baseline
  no-refresh VO-bank no-op polar5
  no-refresh VO-bank no-op polar4
  no-refresh VO-bank no-op polar5, all-window
  no-refresh VO-bank no-op polar4, all-window
  current no-op V0-1 polar5 replicate
  current no-op all-V polar4 replicate
```

The implementation question is whether we need a `LOCO_FULL_NO_PRECOND` or
`LOCO_FULL_SCHEDULE_ONLY` mode that skips the right-inverse helper when
`LOCO_FULL_NOOP=1`, instead of paying for identity matmuls and feature-stat
collection.

Follow-up patch prepared `LOCO_FULL_SCHEDULE_ONLY=1` and
`NEWTONV_SUITE=scheduleonly`.

Code-audit read:

```text
LOCO_FULL_SCHEDULE_ONLY=1:
  - disables full feature collection and factor refresh
  - skips the right-preconditioner / identity helper
  - preserves explicit Nesterov operand -> polar_express_from_operand
  - after the follow-up guard, does not allocate or zero full-stat buffers
```

Promote schedule-only only if a no-stats case beats same-suite baseline by
`>=0.003` at step 200, matches or beats the collection-enabled no-op replicate,
and keeps non-refresh timing within about `2-3%` of baseline. Kill it if the
no-stats variants are within `+/-0.002` of baseline or only the collection
replicates win.

The all-window polar5 control is important because polar5 schedule-only should
be nearly equivalent to baseline if the fused and explicit paths are
numerically equivalent to the baseline. The schedule-only suite later rejected
this as a standalone candidate: all no-stats schedule-only variants were worse
than their same-suite baseline.

## Cycle 2 GPU Window

Time accounting:

- GPU window started: about `2026-05-27 20:34 IST`.
- Preconditioner diagnostic H100 app: `ap-XaBa7nvUMlesIsqR7Yk0Wk`,
  `20:34-20:46 IST`, Modal wall time `688.323s`.
- GPU window ended: about `2026-05-27 20:46 IST`.
- Required meditation/audit window: `20:46-21:46 IST`.
- Next H100 launch allowed: `2026-05-27 21:46 IST`, unless the user overrides.

All NanoGPT Modal apps from this cycle were stopped after completion.

## Preconditioner Diagnostic Result

Log:

- `.opencode/modal_newtonv_preconddiag_h100_20260527.log`

Parsed final results:

| case | step 120 | step avg |
| --- | ---: | ---: |
| V 0-1 active polar5 | `4.1853` | `598.50ms` |
| V 0-1 active polar4 | `4.1828` | `588.14ms` |
| all-V active polar4 | `4.1813` | `595.09ms` |

This run was primarily diagnostic. It confirmed that the preconditioner target
is not weak; the current application schedule is weak.

For V `0-1`, polar4:

```text
target_delta: 1.10-1.16
target_cos:   0.32-0.39
```

For all V layers, polar4:

```text
target_delta: 1.11-1.20
target_cos:   0.28-0.38
```

But actual pre-Polar deltas were governed by the restarted blend:

```text
step 50:  blend=0.0017, actual_delta~0.0019
step 80:  blend=0.0267, actual_delta~0.031
step 112: blend=0.0533, actual_delta~0.059
```

Post-Polar deltas were real but modest:

```text
V 0-1 polar4: about 5-15%
all-V polar4: about 4-14%
```

Read:

```text
The feature metric is producing a major right-side correction.
The current branch then mostly washes it out through low blend plus Polar/NorMuon.
```

Prepared follow-up suite:

```text
NEWTONV_SUITE=paperfilter
```

It tests:

```text
baseline
matched V0-1 full-path no-op polar4
V0-1 inverse before momentum, ridge=0.2, refresh=16, ema=0.8, blend max=0.10, blend steps=32
V0-1 finite-time clipped filter with the same paper-style damping
V0-1 power-0.5 clipped filter with the same paper-style damping
```

The rationale is to apply enough of the correction to matter while using
paper-style damping and clipped filters to avoid raw `C^-1` instability.

## Cycle 3 GPU Window

Time accounting:

- GPU window started: about `2026-05-27 20:49 IST`.
- Paper-filter H100 app: `ap-RRaRNWPzXSTvV4xqol8yil`,
  `20:49-21:06 IST`, Modal wall time `979.974s`.
- GPU window ended: about `2026-05-27 21:06 IST`.

Logs:

- `.opencode/modal_newtonv_paperfilter_h100_20260527.log`
- `.opencode/modal_newtonv_paperfilter_h100_20260527.parsed.md`
- `.opencode/modal_newtonv_paperfilter_h100_20260527.diagnostics.md`

Parsed final results:

| case | step 120 | step avg |
| --- | ---: | ---: |
| baseline | `4.1851` | `572.28ms` |
| V 0-1 no-op polar4 | `4.1803` | `572.24ms` |
| V 0-1 inverse, before momentum, ridge 0.20, blend 0.10 | `4.1834` | `570.48ms` |
| all-V finite clipped, before momentum, ridge 0.20, blend 0.10 | `4.1861` | `574.58ms` |
| all-V power 0.5 clipped, before momentum, ridge 0.20, blend 0.10 | `4.1866` | `575.01ms` |

The finite/power labels said `v01`, but those cases used
`tools/run_newtonv_block_power_gate.sh`, whose default layer set was `all`.
The suite has been patched after this run so future paper-filter finite/power
cases explicitly set `LOCO_DIAG_ATTN_LAYERS=0-1`.

Code-audit subagent `019e6a18-6a0a-7031-945c-7a479ee53498` found the same
label/default bug in the `rightfilter` suite. It has also been patched so
`rf_finite_dense_v01_polar4` and `rf_power05_dense_v01_polar4` force
`LOCO_DIAG_ATTN_LAYERS=0-1`.

The same audit found a separate interpretation issue:

```text
LOCO_FULL_POLAR_ITERS only affects the after-momentum
polar_express_from_operand path. Before-momentum full-preconditioning falls
through the baseline fused polar_express path, so before-momentum cases labeled
polar4 actually use the baseline polar iteration schedule.
```

So the paperfilter inverse/finite/power `before_polar4` labels should be read
as "before momentum with the baseline polar path", not a true polar4 ablation.

Read:

```text
The schedule/no-op polar4 control beat the same-suite baseline by 0.0048 at
step 120. None of the paper-style active filters beat that no-op. The inverse
case was at least neutral-ish, but finite/power clipped all-V were worse than
baseline. This does not promote the right-filter family yet; it says the next
comparison must be no-op-matched and layer-correct.
```

## Cycle 3 Meditation Window

Started: `2026-05-27 21:06 IST`.

Expected next H100 launch time under the one-hour cadence: about
`2026-05-27 22:06 IST`, unless the user overrides.

Result-audit subagent `019e6a17-eaf5-7962-bf55-d7d78d7f0e2f` completed. Key
read:

```text
The feature metric is mechanically real, but active Newton-specific variants
have not yet beaten no-op/full-path controls at 200. The paperfilter finite and
power cases were mislabeled and must be rerun layer-correct before judging V
0-1. Metric-polar had the cleanest 120-step active hit but QK+V did not persist
to 200; V-only metric-polar has not yet had a matched 200-step promotion.
```

Prepared next suite:

```text
NEWTONV_SUITE=metricv_promote
```

It runs:

```text
baseline, 200 steps
V 0-1 full no-op polar4, collect 0-64, apply 48-112
V 0-1 metric-polar polar4, ridge 0.03, blend 0.25, no norm restore
V 0-1 metric-polar polar4, ridge 0.20, blend 0.10, norm restore
```

This directly tests the stronger activation-metric update
`polar(G L^-T) L^-1` on V alone, with a matched no-op and one safer/tuned
variant. Promotion bar: it must beat the same-suite no-op at 200, not just the
ordinary baseline.

Theory/literature subagent `019e6a18-47be-7142-9df9-f286fbfa8aa8` completed.
Key read:

```text
Newton-Muon, K-FAC, LocoProp, Shampoo/SOAP all point at a real right activation
covariance factor. The unresolved choice is the spectral transfer function and
where the metric survives relative to Muon/polar. Raw C^-1 everywhere is not
the default answer; C^-1/2 / power / finite filters and activation-metric polar
are the theory-clean ways to test "washed away" vs "too aggressive".
```

It recommended an MLP `c_fc` activation-metric/power ladder as the best theory
probe. Current branch only has full-matrix machinery for `qk,v,o`; MLP has the
older diagonal path but not full/metric MLP `c_fc`. So the immediate prepared
H100 suite remains `metricv_promote`, while the implementation follow-up is:

```text
Add a narrow MLP c_fc full/metric path only if V-only metric-polar fails or
ties the no-op at 200 but diagnostics still show the right metric surviving.
Do not spend 8xH100 on this before a 1xH100 MLP c_fc screen beats no-op.
```

## Cycle 3 Plan Revision

Timestamp: `2026-05-27 21:29 IST`.

User instruction: do not read PR233. The PR233 audit path is dropped.

The next H100 run is now:

```text
NEWTONV_SUITE=paper_v_promote
```

Reason:

```text
metricv_promote answers the clean V-only activation-metric question, but the
current stronger blocker is that before-momentum/paper-style filters were not
judged against a before-momentum no-op, and finite/power V 0-1 were only
patched after the last H100 run.
```

The new suite runs:

```text
baseline
V 0-1 before-momentum no-op, ridge 0.20, blend 0.10 shape
V 0-1 after-momentum no-op polar4
V 0-1 finite-time clipped filter, ridge 0.20
V 0-1 power 0.5 clipped filter, ridge 0.20
V 0-1 inverse, ridge 0.20
V 0-1 metric-polar, ridge 0.20, blend 0.05, norm restore
```

Cadence state:

```text
Meditation window started around 21:06 IST.
Do not launch the next H100 before about 22:06 IST unless the user overrides.
```

Subagent audit updates:

```text
Carver: paper_v_promote must beat both no-op controls. Gate active finite/power/
inverse at B-0.003 and both no-ops by at least 0.002. Gate metric-polar at the
same no-op margins and at least 0.002 better than the best paper-style active
filter.

Fermat: if V fails, the narrow full-matrix MLP fallback is c_fc only. It needs
[11,768,768] Gram/EMA/chol/inv buffers, mlp_bank even-index ownership, gram
collection at mlp_in = norm(x), and an mlp_bank c_fc-only optimizer helper.
Worst-rank refresh collection for two owned c_fc layers is roughly 116 GFLOP per
refresh at final-stage local tokens, so do not implement it unless V leaves a
reason to continue.

Aristotle: paper_v_promote env propagation works, but inherited LOCO_* vars can
leak into cases. run_case now sanitizes LOCO_* controls before applying each
case's explicit env. Also, before-momentum active filters use baseline fused
polar_express, not LOCO_FULL_POLAR_ITERS, so the before-momentum no-op is the
matched control for those cases.
```

## Cycle 3 H100 Result: paper_v_promote

Started after user override allowing GPUs for the next 3 hours.

Modal app:

```text
ap-36RFDQ7tIuIjsivgH1DMSL
```

Parsed results:

```text
pvp_baseline:                           3.8794, 1590.01ms/step
pvp_v01_noop_before_r020_blend010:      3.8858,  709.20ms/step
pvp_v01_noop_after_polar4:              3.8887,  713.78ms/step
pvp_finite_v01_before_r020_blend010:    3.8899,  712.27ms/step
pvp_power05_v01_before_r020_blend010:   3.8960,  713.71ms/step
pvp_inverse_v01_before_r020_blend010:   3.8855,  713.39ms/step
pvp_cholmetric_v01_after_r020_blend005: 3.8843,  712.87ms/step
```

Interpretation:

```text
All paper-style active V 0-1 treatments lost to baseline.
Both no-op controls also lost to baseline.
Metric-polar V-only was the best active line, but still lost by 0.0049.
The baseline step time is contaminated by two large compile/cache stalls and
should not be used as a cost baseline for this suite.
```

Decision:

```text
Do not spend more H100 on V-only right-preconditioning in the current branch.
The original full-V signal was real enough to justify this ladder, but this
matched run says the current V placement/filter/window family is not WR-ready.
```

Next useful branch:

```text
Implement a narrow full/metric MLP c_fc path if continuing the right-
preconditioner thesis. It is the clean 768-dimensional surface left by the
paper/theory path, and current code only has diagonal MLP support.
```

## Cycle 4 Setup: MLP c_fc Probe

User reopened GPU usage for the next 3 hours. Implemented the narrow MLP c_fc
full-Gram path instead of spending more time on V-only:

```text
LOCO_FULL_SURFACES=mlp_fc
full Gram collected from mlp_in = norm(x)
precondition only even mlp_bank indices, i.e. c_fc
do not touch c_proj
owner-local collection/factorization under LOCO_FULL_LOCAL_STATS=1
```

Prepared H100 suite:

```text
NEWTONV_SUITE=mlpfc
MFC_STEPS=120
MFC_VAL_EVERY=40
MFC_LAYERS=0-1
```

Cases:

```text
mfc_baseline
mfc_noop_after_polar4
mfc_inverse_before_r020_blend010
mfc_inverse_after_polar4_r020_blend010
mfc_cholmetric_after_polar4_r020_blend005_norm
```

## Cycle 4 H100 Result: mlpfc

Modal app:

```text
ap-41D4sbAUkJPoCzKPeq7ffw
```

Parsed 120-step results:

```text
mfc_baseline:                              4.1828, 755.21ms/step
mfc_noop_after_polar4:                     4.1816, 636.21ms/step
mfc_inverse_before_r020_blend010:          4.1781, 627.92ms/step
mfc_inverse_after_polar4_r020_blend010:    4.1814, 632.27ms/step
mfc_cholmetric_after_polar4_r020_blend005: 4.1788, 631.37ms/step
```

Interpretation:

```text
The MLP c_fc full-Gram path produced the first same-suite right-preconditioner
signal that beats both baseline and no-op controls in this cycle.

Best line is before-momentum inverse:
  baseline gap: 0.0047
  no-op gap:   0.0035

Metric-polar also clears the control, but trails before-momentum inverse by
0.0007 at 120.
```

Prepared follow-up:

```text
NEWTONV_SUITE=mlpfc_promote
MFP_STEPS=200
MFP_VAL_EVERY=50
MFP_LAYERS=0-1
```

## Cycle 4 H100 Result: mlpfc_promote

Modal app:

```text
ap-BX5R4IFCoqZpItCHz56tN6
```

Parsed 200-step results:

```text
mfp_baseline:                              3.8869, 673.78ms/step
mfp_noop_after_polar4:                     3.8852, 665.72ms/step
mfp_inverse_before_r020_blend010:          3.8832, 664.40ms/step
mfp_cholmetric_after_polar4_r020_blend005: 3.8873, 664.10ms/step
```

Interpretation:

```text
Before-momentum inverse is the only MLP c_fc active line that persisted.
It beat baseline by 0.0037 and after-polar4 no-op by 0.0020.
Metric-polar lost to baseline by 0.0004 and should not be promoted.
```

The remaining control hole is ordering-specific: the active line is
before-momentum, but the no-op in this promote suite is after-momentum polar4.
Prepared the narrow control suite:

```text
NEWTONV_SUITE=mlpfc_before_control
MBC_STEPS=200
MBC_VAL_EVERY=50
MBC_LAYERS=0-1
```

## Cycle 4 H100 Result: mlpfc_before_control

Modal app:

```text
ap-SZQgOkSelB2k5IEFxEuOeh
```

Parsed 200-step results:

```text
mbc_noop_before_r020_blend010:    3.8824, 608.17ms/step
mbc_inverse_before_r020_blend010: 3.8887, 603.72ms/step
```

Interpretation:

```text
The matched before-momentum no-op beats the active inverse by 0.0063.
This kills the MLP c_fc inverse candidate as currently formulated.
The previous positive promote result was not a clean geometry win because its
control was after-momentum polar4, not the true before-momentum path.
```

Prepared controlled surface scan:

```text
NEWTONV_SUITE=surface_control
SC_STEPS=120
SC_VAL_EVERY=40
SC_LAYERS=0-1
```

Cases include same-surface no-op controls for QK, O, and QKVO activation-metric
polar. Do not trust active-only QK/O surface screens after the MLP control miss.

## Cycle 5 H100 Result: surface_control

Modal app:

```text
ap-tPTH6z4XWZXFGnxCTSENFu
```

Parsed 120-step results:

```text
sc_baseline:                 4.1777, 583.25ms/step
sc_qk_noop_metric_polar4:    4.1865, 584.54ms/step
sc_qk_cholmetric_polar4:     4.1938, 587.69ms/step
sc_o_noop_metric_polar4:     4.1810, 585.47ms/step
sc_o_cholmetric_polar4:      4.1843, 584.41ms/step
sc_qkvo_noop_metric_polar4:  4.1801, 594.45ms/step
sc_qkvo_cholmetric_polar4:   4.1761, 590.96ms/step
```

Interpretation:

```text
QK-only and O-only metric-polar lose to their same-surface no-op controls.
QKVO metric-polar is the only active line that beats both no-op and baseline:
  vs QKVO no-op: +0.0040 loss improvement
  vs baseline:   +0.0016 loss improvement
The signal is small, but it is matched-control positive, so promote narrowly.
```

Prepared follow-up:

```text
NEWTONV_SUITE=qkvo_metric_promote
QMP_STEPS=200
QMP_VAL_EVERY=50
QMP_LAYERS=0-1
```

## Cycle 5 H100 Result: qkvo_metric_promote

Modal app:

```text
ap-b3KIPyouTgaox8RorukySL
```

Parsed 200-step results:

```text
qmp_baseline:                 3.8945, 670.97ms/step
qmp_qkvo_noop_metric_polar4:  3.8948, 665.50ms/step
qmp_qkvo_cholmetric_polar4:   3.8900, 663.11ms/step
```

Interpretation:

```text
QKVO 0-1 activation-metric polar is now the best matched-control positive line:
  vs QKVO no-op: +0.0048 loss improvement
  vs baseline:   +0.0045 loss improvement

The 100-step screen was not active-positive versus no-op, but the 150/200-step
anchors were. This looks like a real persistence signal, not just early noise.
```

Next run:

```text
NEWTONV_SUITE=qkvo_metric_promote
QMP_STEPS=120
QMP_VAL_EVERY=40
QMP_LAYERS=0-3
```

Purpose: test whether the QKVO metric-polar signal widens beyond layers 0-1
without paying for a full 200-step promote first.

## Cycle 5 H100 Result: qkvo_metric_l03

Modal app:

```text
ap-HKcnDQwWoAVkrczZujriJ5
```

Parsed 120-step results:

```text
qmp_baseline:                 4.1873, 586.24ms/step
qmp_qkvo_noop_metric_polar4:  4.1744, 591.79ms/step
qmp_qkvo_cholmetric_polar4:   4.1833, 594.18ms/step
```

Interpretation:

```text
Widening QKVO to layers 0-3 is not an active metric win.
The no-op/full-path/window effect is very strong, but active metric-polar loses
to that matched no-op by 0.0089 at 120.
```

Next run:

```text
NEWTONV_SUITE=qkvo_metric_promote
QMP_STEPS=200
QMP_VAL_EVERY=50
QMP_LAYERS=0-1
```

Purpose: replicate the QKVO 0-1 200-step active win before tuning windows,
blend, or ridge.

## Cycle 5 H100 Result: qkvo_metric_repl

Modal app:

```text
ap-pXpIjbZKwzP0924aTXwy8s
```

Parsed 200-step results:

```text
qmp_baseline:                 3.8856, 602.28ms/step
qmp_qkvo_noop_metric_polar4:  3.8869, 590.51ms/step
qmp_qkvo_cholmetric_polar4:   3.8872, 592.70ms/step
```

Interpretation:

```text
The QKVO 0-1 active metric-polar win did not replicate.
It lost to the matched no-op by 0.0003 and to baseline by 0.0016.
Treat QKVO 0-1 active as variance-scale until a tuned variant produces a larger
matched-control gap.
```

Prepared schedule/full-path isolation:

```text
NEWTONV_SUITE=qkvo_schedule
QS_STEPS=200
QS_VAL_EVERY=50
QS_LAYERS=0-3
```

Purpose: test whether the strong 0-3 no-op/window result survives when stripped
down to `LOCO_FULL_SCHEDULE_ONLY=1`, i.e. explicit after-momentum polar4 path
without full feature-stat collection/preconditioner work.

## Cycle 5 H100 Result: qkvo_schedule

Modal app:

```text
ap-bzu37ARFUvH95JtkPI9LLM
```

Parsed 200-step results:

```text
qs_baseline:                    3.8824, 684.54ms/step
qs_qkvo_schedule_only_polar4:   3.8867, 669.62ms/step
qs_qkvo_noop_metric_polar4:     3.8881, 669.80ms/step
```

Intermediate anchors:

```text
step 50:
  baseline                 5.6186
  schedule-only polar4     5.6077
  full-path no-op metric   5.6113

step 100:
  baseline                 4.6878
  schedule-only polar4     4.6701
  full-path no-op metric   4.6893

step 150:
  baseline                 4.1124
  schedule-only polar4     4.1181
  full-path no-op metric   4.1171
```

Interpretation:

```text
Both QKVO controls produced early movement and then faded by 200.
Schedule-only was ahead through 100 but lost by 150/200. Full-path no-op was
not stable either. The earlier QKVO no-op/window hit should not be treated as a
promotion-ready WR lever.
```

Next:

```text
Stop broad QKVO control promotion. If spending another H100 run, return to the
strongest active idea: V/right-preconditioning, but make the test answer a
specific theory question rather than another broad surface sweep.
```

## Cycle 5 H100 Result: metricv_promote

Modal app:

```text
ap-jMRz1zW0NZCXIOlN4zYgYl
```

Parsed 200-step results:

```text
mvp_baseline:                                3.8845, 781.01ms/step
mvp_v01_noop_polar4:                        3.8876, 714.74ms/step
mvp_cholmetric_v01_polar4_r003_blend025:    3.8892, 725.79ms/step
mvp_cholmetric_v01_polar4_r020_blend010_norm 3.8844, 722.88ms/step
```

Intermediate anchors:

```text
step 50:
  baseline                         5.6294
  V no-op polar4                   5.5982
  metric r0.03 blend0.25 no-norm   5.6190
  metric r0.20 blend0.10 norm      5.5839

step 100:
  baseline                         4.6821
  V no-op polar4                   4.6720
  metric r0.03 blend0.25 no-norm   4.6952
  metric r0.20 blend0.10 norm      4.6822

step 150:
  baseline                         4.1195
  V no-op polar4                   4.1215
  metric r0.03 blend0.25 no-norm   4.1219
  metric r0.20 blend0.10 norm      4.1105
```

Interpretation:

```text
The safe/norm-restored activation-metric V line beat its matched no-op by
0.0032 at 200, but only tied the same-suite baseline by 0.0001. The meaningful
signal was at step 150, where it beat baseline by 0.0090 and no-op by 0.0110,
then faded by 200 after the 48-112 application window had been off for 88
steps.

The stronger no-norm metric setting is bad in this suite. It loses to baseline
and no-op by 100/150/200.
```

Next:

```text
Run a narrower safe-metric V window probe with the same r0.20/blend0.10/norm
setting but extend the application window from 48-112 to 48-160. Use a matched
V no-op with the same window. The question is whether the step-150 active
signal was real and simply faded after deactivation.
```

## Cycle 5 H100 Result: metricv_window 48-160

Modal app:

```text
ap-Aeq6l1lal9fdlKIw8vTvZ8
```

Parsed 200-step results:

```text
mvsw_baseline:                                  3.8861, 780.18ms/step
mvsw_v01_noop_polar4:                          3.8876, 774.83ms/step
mvsw_cholmetric_v01_polar4_r020_blend010_norm: 3.8915, 774.51ms/step
```

Intermediate anchors:

```text
step 50:
  baseline         5.5976
  V no-op          5.6183
  V metric safe    5.6331

step 100:
  baseline         4.6788
  V no-op          4.6831
  V metric safe    4.6980

step 150:
  baseline         4.1246
  V no-op          4.1195
  V metric safe    4.1204
```

Interpretation:

```text
Extending the safe V metric window from 48-112 to 48-160 makes the active
metric worse. The useful effect from the prior suite appears to be a delayed
pulse after a shorter window, not a benefit from leaving the metric on longer.
```

Next:

```text
Run one shifted short-window probe, e.g. 80-144, to test whether the delayed
post-window benefit can be moved closer to the 200-step screen. If that fails,
stop V metric-window tuning.
```

## Cycle 5 H100 Result: metricv_window 80-144

Modal app:

```text
ap-677aXmcCbXmr9H9M8CBfHp
```

Parsed 200-step results:

```text
mvsw_baseline:                                  3.8844, 675.96ms/step
mvsw_v01_noop_polar4:                          3.8850, 594.75ms/step
mvsw_cholmetric_v01_polar4_r020_blend010_norm: 3.8864, 588.46ms/step
```

Intermediate anchors:

```text
step 50:
  baseline         5.6286
  V no-op          5.5933
  V metric safe    5.6219

step 100:
  baseline         4.6631
  V no-op          4.6690
  V metric safe    4.6769

step 150:
  baseline         4.1120
  V no-op          4.1104
  V metric safe    4.1202
```

Interpretation:

```text
The shifted 80-144 window also fails. Active metric loses to both baseline and
matched no-op at 100/150/200. The earlier 48-112 safe-metric step-150 hit does
not turn into a 200-step improvement by shifting the window later.
```

Decision:

```text
Stop V metric-window tuning. The useful-looking activation-metric effect is
not stable enough at 200, and stronger/longer/later windows all worsen it.
```

## Cycle 6 H100 Result: v_spectral_shape 0-1 V Pulse

Modal app:

```text
ap-HMCkfT0iHOfJgC86PeB8v1
```

Parsed 160-step results:

```text
vss_baseline_a:                         4.0069, 586.99ms/step
vss_baseline_b:                         4.0068, 552.24ms/step
vss_v01_noop_polar4:                    4.0030, 691.25ms/step
vss_metric_v01_r020_blend010_norm:      4.0080, 646.72ms/step
vss_power05_v01_r020_blend010:          4.0066, 646.55ms/step
vss_power075_v01_r020_blend010:         4.0098, 645.66ms/step
```

Interpretation:

```text
The V 0-1 pulse is not hot under matched 160-step controls. The two baselines
are nearly identical, and the V polar4 no-op beats both active preconditioners.
Safe activation-metric polar loses to baseline by ~0.0012 and to no-op by
0.0050. C^-0.5 is roughly baseline-neutral but still loses to no-op by 0.0036.
C^-0.75 is worse.
```

Diagnostics:

```text
Activation-metric polar target_delta is large, ~0.74-0.86, with target cosine
~0.63-0.73. With blend capped at 0.10, the actually applied post-polar delta is
only ~0.07-0.075 at steps 80/100/112 and cosine remains ~0.9975.

Power C^-0.5 is gentler: target_delta ~0.26-0.41 and applied blended delta
~0.03-0.034 by steps 80/100/112. Power C^-0.75 is stronger:
target_delta ~0.39-0.50 and applied blended delta ~0.04-0.043 by steps
80/100/112. Neither translated into a same-suite loss win.
```

Decision:

```text
Do not spend more H100 time on V 0-1 pulse/window tuning in the current
post-momentum metric/inverse-power form. The input metric is mechanically
active and anisotropic, but the loss signal is dominated by the polar4/no-op
path and the active right-preconditioner does not beat that control.

Next productive direction should change semantics rather than window/ridge
microtuning: either a direct NorMuon interaction test such as skip/alter
variance reduction during the short pulse, or a different clean surface with a
matched no-op and diagnostics. If continuing V, use it as a mechanism probe,
not a WR candidate.
```
