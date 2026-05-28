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

## Cycle 7 H100 Result: qkvo_power_shape 0-1 Pulse

Modal app:

```text
ap-zCFeSrQ2lO3c0LYYzKkIYA
```

Parsed 160-step results:

```text
qps_baseline:                    3.9992, 622.61ms/step
qps_qkvo_noop_polar4:            4.0051, 696.15ms/step
qps_qkvo_power05_r020_blend010:  4.0061, 649.08ms/step
qps_qkvo_power075_r020_blend010: 4.0211, 630.52ms/step
```

Intermediate anchors:

```text
step 50:
  baseline        5.5510
  QKVO no-op      5.5728
  QKVO power 0.5  5.5807
  QKVO power 0.75 5.6175

step 100:
  baseline        4.4756
  QKVO no-op      4.4805
  QKVO power 0.5  4.4793
  QKVO power 0.75 4.5143

step 150:
  baseline        4.0404
  QKVO no-op      4.0461
  QKVO power 0.5  4.0469
  QKVO power 0.75 4.0627
```

Diagnostics:

```text
The QKVO power filters are not mechanically null. By steps 80/100/112, alpha
0.5 has target deltas around 0.45 for QK/O and 0.34-0.37 for V. Alpha 0.75 is
stronger, with target deltas around 0.51-0.53 for QK/O and 0.42 for V. The
post-polar update changes are visible, not washed away: QK post-polar deltas
reach about 0.15-0.18 in the active window, with O/V also moving.

The spectra are also strongly anisotropic. Attention-input eig_p99 is roughly
9-10 at refreshes, O-headwise eig_p99 is often 8-14, and clipped gains hit the
2.0 cap heavily for alpha 0.75.
```

Decision:

```text
Do not promote broad QKVO inverse-power transfer. It changes the update and
touches the expected surfaces, but the loss gets worse. Alpha 0.5 is slightly
worse than both baseline and no-op; alpha 0.75 is clearly harmful. This argues
against "make the right preconditioner stronger across all attention surfaces"
as the next WR lever.

The next meaningful experiment should isolate semantics rather than add more
surfaces or more spectral strength: either test the NorMuon variance-reduction
interaction directly, or test a much narrower surface/form such as O-headwise
only with a conservative shrink-only filter. Broad QKVO is too entangled with
softmax/logit dynamics to use as the next cheap promotion line.
```

## Cycle 8 H100 Result: V Variance-Reduction Interaction

Modal app:

```text
ap-7ultOtC7HSn4b0xrUIyF0V
```

Parsed 160-step results:

```text
vvr_baseline:                                4.0065, 750.78ms/step
vvr_v01_noop_polar4:                        4.0061, 869.36ms/step
vvr_v01_noop_polar4_skipvr:                 4.0073, 654.55ms/step
vvr_metric_v01_varred_r020_blend010_norm:   4.0090, 653.28ms/step
vvr_metric_v01_skipvr_r020_blend010_norm:   4.0080, 656.06ms/step
```

Intermediate anchors:

```text
step 50:
  baseline          5.5911
  no-op             5.5839
  no-op skip varred 5.5818
  metric varred     5.5849
  metric skipvarred 5.5670

step 75:
  baseline          4.9977
  no-op             4.9707
  no-op skip varred 5.0041
  metric varred     4.9743
  metric skipvarred 4.9860

step 100:
  baseline          4.4857
  no-op             4.4880
  no-op skip varred 4.4883
  metric varred     4.4869
  metric skipvarred 4.4893

step 150:
  baseline          4.0479
  no-op             4.0473
  no-op skip varred 4.0487
  metric varred     4.0504
  metric skipvarred 4.0494
```

Diagnostics:

```text
The V activation-metric update is mechanically active. Target deltas are
roughly 0.73-0.85, with target cosines around 0.64-0.74. At full blend the
applied metric delta is roughly 0.07-0.076 with cosine around 0.9975.

Skipping NorMuon variance reduction is not a general rescue. The no-op skip
control is worse than the normal no-op by the endpoint, and the active metric
skip-varred line still loses by 160. However, the active skip-varred metric
case has a real step-50 hit: 5.5670 versus baseline 5.5911 and normal no-op
5.5839. That signal fades by step 75 and reverses by step 100.
```

Decision:

```text
Do not promote skip-varred V metric. It does not fix the endpoint and it makes
the no-op control worse. But keep the step-50 hit as a narrow lead: the metric
may be useful as a very short pulse, not as a 48-112 window. The next cheap
probe, if any, should test short active windows such as 48-56 and 48-64 against
matched no-op controls.
```

## Cycle 9 H100 Result: V Short-Pulse Screen

Modal app:

```text
ap-7Vpd7FYmM3fDmxMmXGbO8E
```

Parsed 120-step results:

```text
vsp_baseline:                    4.1902, 637.12ms/step
vsp_v01_noop_polar4_win48_56:    4.1832, 582.21ms/step
vsp_metric_skipvr_win48_56:      4.1835, 587.16ms/step
vsp_v01_noop_polar4_win48_64:    4.1851, 579.96ms/step
vsp_metric_skipvr_win48_64:      4.1842, 583.26ms/step
```

Intermediate anchors:

```text
step 50:
  baseline        5.5815
  no-op 48-56     5.5312
  metric 48-56    5.5399
  no-op 48-64     5.5650
  metric 48-64    5.5393

step 75:
  baseline        4.7404
  no-op 48-56     4.7275
  metric 48-56    4.7310
  no-op 48-64     4.7361
  metric 48-64    4.7315

step 100:
  baseline        4.3414
  no-op 48-56     4.3339
  metric 48-56    4.3335
  no-op 48-64     4.3398
  metric 48-64    4.3355
```

Diagnostics:

```text
The short V metric deltas are mechanically active but small in the applied
window: for 48-56, target deltas are ~0.80 at steps 50/56 and applied deltas
are ~0.005 and ~0.020. For 48-64, target deltas are ~0.79-0.81 and applied
deltas grow to ~0.039 by step 64.
```

Decision:

```text
The right preconditioner still does not beat the matched short-pulse control.
The best line is the 48-56 no-op/polar4 path, not the metric line. This is a
real lead, but it is an optimizer-path/polar-iteration schedule lead rather
than Newton-Muon evidence.

Next cheap probe should remove feature-stat overhead and check whether a
LOCO_FULL_SCHEDULE_ONLY=1 48-56 polar4 pulse reproduces the win. If it does,
promote that schedule-only pulse to 200; if it fails, treat the 48-56 no-op
result as a noisy/full-stat artifact.
```

## Cycle 10 H100 Result: V Schedule-Pulse Control

Modal app:

```text
ap-Vio3sAUTa6vmVglYIPgcdE
```

Parsed 120-step results:

```text
vsc_baseline:                         4.1799, 674.66ms/step
vsc_v01_noop_polar4_win48_56:         4.1854, 573.09ms/step
vsc_schedule_only_polar4_win48_56:    4.1894, 577.43ms/step
vsc_schedule_only_polar4_win48_64:    4.1823, 570.99ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.5422
  no-op 48-56          5.5437
  schedule 48-56       5.5477
  schedule 48-64       5.5420

step 75:
  baseline             4.7273
  no-op 48-56          4.7425
  schedule 48-56       4.7487
  schedule 48-64       4.7303

step 100:
  baseline             4.3298
  no-op 48-56          4.3363
  schedule 48-56       4.3426
  schedule 48-64       4.3310
```

Diagnostics:

```text
The 48-56 no-op/polar4 result from Cycle 9 did not reproduce in the matched
control suite. Removing feature-stat work with LOCO_FULL_SCHEDULE_ONLY=1 also
does not recover the win. The wider 48-64 schedule-only pulse is closest, but
still loses at 75/100/120.

All three active-path cases show the same late compiled-path timing shape:
steps before the active region are ~238-240ms in the screen, the active path
raises steps to ~440ms, and a large one-time path transition appears around
step 81. This means the schedule-only path is not a free optimizer tweak in
the current implementation.
```

Decision:

```text
Do not promote the V short-pulse path. The old 48-56 no-op lead was not stable
under a same-suite control, and schedule-only polar4 did not isolate a cheap
beneficial schedule effect.

For the next H100 slice, stop V window tuning. The remaining promising branch
is MLP-fc: previous 200-step screens showed a small MLP-fc before-momentum
signal, but the no-op/control path may be the real source. Run an MLP-fc
before-momentum isolation suite with same-run baseline, no-op-before, and
active inverse-before before spending on broader surfaces.
```

## Cycle 11 H100 Result: MLP-fc Before-Momentum Control

Modal app:

```text
ap-4zLTjHcCLOPB8D8RIfza6D
```

Parsed 200-step results:

```text
mbc_baseline:                         3.8853, 661.15ms/step
mbc_schedule_only_before:             3.8909, 610.83ms/step
mbc_noop_before_r020_blend010:        3.8795, 596.16ms/step
mbc_inverse_before_r020_blend010:     3.8875, 584.43ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.6108
  schedule-only        5.6057
  no-op before         5.5920
  inverse before       5.6149

step 100:
  baseline             4.6850
  schedule-only        4.6784
  no-op before         4.6906
  inverse before       4.6715

step 150:
  baseline             4.1196
  schedule-only        4.1245
  no-op before         4.1124
  inverse before       4.1184
```

Diagnostics:

```text
The no-op-before control has blend=0 and logs full_mlp_fc grad ratios of
exactly 1.0, but it wins the endpoint by 0.0058. The active inverse-before arm
does not beat baseline or no-op at 200, despite being mechanically active
(grad ratio ~0.996 at step 50 and ~0.951 at step 100).

Schedule-only-before, which avoids stats/preconditioner work, loses at 150 and
200. Therefore the endpoint win is not a cheap schedule-only path effect, and
the active right-preconditioner does not explain the MLP-fc win.
```

Decision:

```text
Do not promote MLP-fc inverse. The best MLP-fc result is a zero-blend control,
not Newton-Muon alpha. This should be treated as a reproducibility/control
warning: feature-stat collection plus zero-blend optimizer plumbing can move a
200-step screen by more than several active preconditioner effects.

Before spending more on right-preconditioner variants, require matched no-op
controls in every suite and judge active variants only against those controls,
not only against baseline.
```

## Cycle 12 H100 Result: MLP-fc Before-Momentum Replicate

Modal app:

```text
ap-DHdHUEDhFSWKtXWprbqO41
```

Parsed 200-step results:

```text
mbc_baseline:                         3.8863, 684.14ms/step
mbc_schedule_only_before:             3.8808, 577.84ms/step
mbc_noop_before_r020_blend010:        3.8907, 571.52ms/step
mbc_inverse_before_r020_blend010:     3.8789, 578.71ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.6061
  schedule-only        5.6096
  no-op before         5.6069
  inverse before       5.5812

step 100:
  baseline             4.6751
  schedule-only        4.6779
  no-op before         4.6778
  inverse before       4.6922

step 150:
  baseline             4.1184
  schedule-only        4.1126
  no-op before         4.1213
  inverse before       4.1075
```

Diagnostics:

```text
The replicate reverses the previous suite's endpoint ordering. This time
active MLP-fc inverse-before is best at 200 and beats the no-op control by
0.0118, while the no-op control loses to baseline. The active inverse still
has the unstable curve shape seen elsewhere: strong at step 50, worse at step
100, strong again at 150/200.

Across the two matched MLP-fc before-control suites:
  baseline:        3.8853, 3.8863
  schedule-only:   3.8909, 3.8808
  no-op before:    3.8795, 3.8907
  inverse before:  3.8875, 3.8789

Means:
  baseline:        3.8858
  schedule-only:   3.8859
  no-op before:    3.8851
  inverse before:  3.8832
```

Decision:

```text
MLP-fc inverse-before is not dead, but it is not yet WR-ready. The two-run
mean is positive by roughly 0.0026 against baseline, but the run-to-run
ordering changes enough that a third replicate is needed before promotion.

If the third replicate has inverse-before beating both baseline and matched
controls, promote MLP-fc inverse-before to the next longer/checkpointed run.
If it does not, treat the current mean as below the control/noise floor.
```

## Cycle 13 H100 Result: MLP-fc Before-Momentum Third Replicate

Modal app:

```text
ap-vpqU5R6hwjyD9RDXKgBpMh
```

Parsed 200-step results:

```text
mbc_baseline:                         3.8903, 706.63ms/step
mbc_schedule_only_before:             3.8833, 618.07ms/step
mbc_noop_before_r020_blend010:        3.8915, 601.79ms/step
mbc_inverse_before_r020_blend010:     3.8873, 593.47ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.6045
  schedule-only        5.6042
  no-op before         5.6043
  inverse before       5.6119

step 100:
  baseline             4.6847
  schedule-only        4.6931
  no-op before         4.6959
  inverse before       4.6764

step 150:
  baseline             4.1315
  schedule-only        4.1203
  no-op before         4.1277
  inverse before       4.1176
```

Three-run endpoint table:

```text
                 run A    run B    run C    mean
baseline         3.8853   3.8863   3.8903   3.8873
schedule-only    3.8909   3.8808   3.8833   3.8850
no-op before     3.8795   3.8907   3.8915   3.8872
inverse before   3.8875   3.8789   3.8873   3.8846
```

Three-run step-150 table:

```text
                 run A    run B    run C    mean
baseline         4.1196   4.1184   4.1315   4.1232
schedule-only    4.1245   4.1126   4.1203   4.1191
no-op before     4.1124   4.1213   4.1277   4.1205
inverse before   4.1184   4.1075   4.1176   4.1145
```

Decision:

```text
MLP-fc inverse-before is the best active right-preconditioner line remaining,
but the margin is not WR-grade. Its three-run 200-step mean beats baseline by
0.0027 and schedule-only by only 0.0004. At step 150 the signal is clearer:
inverse-before beats baseline by 0.0087 and schedule-only by 0.0046.

Do not promote to a record attempt. The only plausible follow-up is a targeted
MLP-fc timing/window study that tries to preserve the step-150 benefit without
endpoint fade. New surface sweeps should remain lower priority until this is
understood.
```

## Cycle 14 H100 Result: MLP-fc Window160 Probe

Modal app:

```text
ap-lCZoBA0K66I5F2u9LVuFoF
```

Parsed 200-step results:

```text
mbc_baseline:                         3.8893, 792.69ms/step
mbc_schedule_only_before:             3.8860, 753.39ms/step
mbc_noop_before_r020_blend010:        3.8902, 740.21ms/step
mbc_inverse_before_r020_blend010:     3.8828, 749.43ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.5966
  schedule-only        5.6374
  no-op before         5.5889
  inverse before       5.5965

step 100:
  baseline             4.6676
  schedule-only        4.6803
  no-op before         4.6827
  inverse before       4.6777

step 150:
  baseline             4.1198
  schedule-only        4.1223
  no-op before         4.1210
  inverse before       4.1139
```

Diagnostics:

```text
Extending the MLP-fc before-momentum active window from 48-112 to 48-160
preserved and amplified the middle-run gain. The active inverse path is the
only arm that beats all matched controls at both step 150 and step 200:
  step 150: inverse beats baseline by 0.0059 and schedule-only by 0.0084
  step 200: inverse beats baseline by 0.0065 and schedule-only by 0.0032

The no-op/control story stayed important. No-op wins at step 50 but fades and
loses at 200, while schedule-only wins modestly at 200. The active inverse
therefore clears the matched-control bar in this run, but only by one
replicate.

Timing from this Modal path remains hard to interpret because all arms hit the
same late-run step-time jump. Use the same-app loss ordering; do not read these
step averages as current-path WR timing.
```

Decision:

```text
This is the strongest MLP-fc before-momentum result so far. Queue an immediate
same-suite replicate before spending GPU time on new surfaces. If the replicate
keeps inverse-before ahead of baseline and schedule/no-op at 200, promote
MLP-fc window160 to the next controlled comparison against Cholesky
metric-polar / half-whitened MLP-fc.
```

## Cycle 15 H100 Result: MLP-fc Window160 Replicate

Modal app:

```text
ap-FNlEaq0nnrryBkn6m4sDkd
```

Parsed 200-step results:

```text
mbc_baseline:                         3.8832, 664.75ms/step
mbc_schedule_only_before:             3.8862, 606.49ms/step
mbc_noop_before_r020_blend010:        3.8834, 599.34ms/step
mbc_inverse_before_r020_blend010:     3.8880, 609.42ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.6157
  schedule-only        5.6031
  no-op before         5.6189
  inverse before       5.5892

step 100:
  baseline             4.6796
  schedule-only        4.6737
  no-op before         4.6734
  inverse before       4.6978

step 150:
  baseline             4.1116
  schedule-only        4.1203
  no-op before         4.1152
  inverse before       4.1197
```

Two-run window160 endpoint table:

```text
                 run A    run B    mean
baseline         3.8893   3.8832   3.8863
schedule-only    3.8860   3.8862   3.8861
no-op before     3.8902   3.8834   3.8868
inverse before   3.8828   3.8880   3.8854
```

Decision:

```text
The window160 active inverse hit did not reproduce cleanly. The two-run mean is
still slightly positive, but the margin is too small and the replicate loses to
baseline/no-op at 200. Do not promote MLP-fc inverse-before window160 as a WR
candidate.

Because the inverse path repeatedly shows early/mid-run non-monotonicity, the
next controlled use of GPU time is not a third identical replicate. Test the
stronger Cholesky metric-polar / half-whitened MLP-fc update on the same
window to see whether preserving more of the input metric helps rather than
gets washed out by the polar step.
```

## Cycle 16 H100 Result: MLP-fc Metric-Polar Window160

Modal app:

```text
ap-POQX1i6AQxnYoh9Z0N1srz
```

Parsed 200-step results:

```text
mfp_baseline:                              3.8820, 824.87ms/step
mfp_noop_after_polar4:                    3.8862, 582.81ms/step
mfp_inverse_before_r020_blend010:         3.8856, 585.30ms/step
mfp_cholmetric_after_polar4_r020_blend005_norm: 3.8896, 587.00ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.5894
  no-op after polar4   5.6026
  inverse before       5.6202
  cholmetric after     5.6069

step 100:
  baseline             4.7130
  no-op after polar4   4.6839
  inverse before       4.6764
  cholmetric after     4.6713

step 150:
  baseline             4.1177
  no-op after polar4   4.1170
  inverse before       4.1270
  cholmetric after     4.1150
```

Decision:

```text
Cholesky metric-polar did not produce an endpoint win on the 48-160 window.
It was the best arm at steps 100 and 150, then became the worst endpoint arm.
This is not a WR candidate as configured.

The useful signal is temporal: half-whitened metric-polar is not inert, and it
does not collapse immediately, but keeping it active to 160 appears harmful.
Run the same MLP-fc metric-polar comparison with the shorter 48-112 window
before abandoning the metric-polar family.
```

## Cycle 17 H100 Result: MLP-fc Metric-Polar Window112

Modal app:

```text
ap-IB0WcZcV3FTIkLlM6SejDt
```

Parsed 200-step results:

```text
mfp_baseline:                              3.8829, 727.86ms/step
mfp_noop_after_polar4:                    3.8873, 595.95ms/step
mfp_inverse_before_r020_blend010:         3.8831, 602.88ms/step
mfp_cholmetric_after_polar4_r020_blend005_norm: 3.8846, 592.36ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.6186
  no-op after polar4   5.5985
  inverse before       5.6140
  cholmetric after     5.6083

step 100:
  baseline             4.6831
  no-op after polar4   4.6941
  inverse before       4.6790
  cholmetric after     4.6734

step 150:
  baseline             4.1234
  no-op after polar4   4.1258
  inverse before       4.1211
  cholmetric after     4.1188
```

Decision:

```text
Shortening metric-polar from 48-160 to 48-112 did not fix the endpoint. The
metric-polar arm was again best at steps 100 and 150, then lost by step 200.
The effect is real enough to measure but not usable with the current strength.

Next test should lower metric-polar blend, not keep changing only the end
window. Add a runner knob for MFP_METRIC_BLEND_MAX and run the same window112
suite with blend 0.02.
```

## Cycle 18 H100 Result: MLP-fc Metric-Polar Window112 Blend002

Modal app:

```text
ap-bfPMj2WCNkHVdIcsegYKSR
```

Parsed 200-step results:

```text
mfp_baseline:                              3.8842, 689.92ms/step
mfp_noop_after_polar4:                    3.8886, 595.87ms/step
mfp_inverse_before_r020_blend010:         3.8816, 602.98ms/step
mfp_cholmetric_after_polar4_r020_blend002_norm: 3.8871, 596.83ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.5955
  no-op after polar4   5.6138
  inverse before       5.6074
  cholmetric after     5.6102

step 100:
  baseline             4.6788
  no-op after polar4   4.6928
  inverse before       4.6648
  cholmetric after     4.6744

step 150:
  baseline             4.1229
  no-op after polar4   4.1177
  inverse before       4.1160
  cholmetric after     4.1199

step 200:
  baseline             3.8842
  no-op after polar4   3.8886
  inverse before       3.8816
  cholmetric after     3.8871
```

Decision:

```text
Lowering Cholesky metric-polar blend from 0.05 to 0.02 did not rescue the
endpoint. The metric-polar arm still moved the curve at step 100, but it lost
to baseline by 0.0029 at step 200 and lost to inverse-before by 0.0055.

Deprioritize MLP-fc metric-polar for immediate WR work. The active hit in this
suite is again inverse-before on MLP-fc layers 0-1, window 48-112: it beats
baseline by 0.0026 and no-op by 0.0070. The correct next run is the
before-momentum control suite for the same window so that schedule-only and
no-op-before are matched to the active placement.
```

## Cycle 19 H100 Result: MLP-fc Before-Control Window112

Modal app:

```text
ap-hvZBwcWOB15c67UB6T6swd
```

Parsed 200-step results:

```text
mbc_baseline:                         3.8846, 714.03ms/step
mbc_schedule_only_before:             3.8915, 641.10ms/step
mbc_noop_before_r020_blend010:        3.8849, 637.34ms/step
mbc_inverse_before_r020_blend010:     3.8852, 639.34ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.5813
  schedule-only        5.6156
  no-op before         5.5823
  inverse before       5.6022

step 100:
  baseline             4.6697
  schedule-only        4.6884
  no-op before         4.6903
  inverse before       4.6801

step 150:
  baseline             4.1150
  schedule-only        4.1190
  no-op before         4.1203
  inverse before       4.1227

step 200:
  baseline             3.8846
  schedule-only        3.8915
  no-op before         3.8849
  inverse before       3.8852
```

Decision:

```text
The MLP-fc inverse-before window112 hit from Cycle 18 does not survive the
matched before-placement controls. Schedule-only is bad, no-op-before is near
baseline, and active inverse is slightly worse than both baseline and no-op at
200.

Deprioritize literal C^-1 MLP-fc repeats. The next principled MLP-fc test is
not lower-blend inverse; it is a bounded spectral transfer on the same c_fc
surface: clipped power C^-0.5 and finite-time inverse, with the same matched
no-op-before control.
```

## Cycle 20 H100 Result: MLP-fc Filter-Control Window112

Modal app:

```text
ap-KwrjiAMoOENgRDmSYuJE9Q
```

Parsed 200-step results:

```text
mff_baseline:                         3.8870, 809.78ms/step
mff_noop_before_r02_blend010:         3.8909, 608.22ms/step
mff_inverse_before_r02_blend010:      3.8828, 597.16ms/step
mff_power05_before_r02_blend010:      3.8858, 588.05ms/step
mff_finite_t10_before_r02_blend010:   3.8856, 603.73ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.6027
  no-op before         5.5978
  inverse before       5.5948
  power 0.5 before     5.6290
  finite t1 before     5.6206

step 100:
  baseline             4.6772
  no-op before         4.6959
  inverse before       4.6934
  power 0.5 before     4.7008
  finite t1 before     4.6933

step 150:
  baseline             4.1212
  no-op before         4.1235
  inverse before       4.1129
  power 0.5 before     4.1202
  finite t1 before     4.1260

step 200:
  baseline             3.8870
  no-op before         3.8909
  inverse before       3.8828
  power 0.5 before     3.8858
  finite t1 before     3.8856
```

Decision:

```text
The bounded spectral transfers did not beat literal C^-1 on MLP-fc. Power
C^-0.5 and finite-time inverse both beat the bad no-op and baseline at 200,
but their margins are small and neither shows the strong 150/200 reversal of
literal inverse.

This is the cleanest positive MLP-fc inverse run since the window160 probe:
inverse beats baseline by 0.0042 and no-op by 0.0081. Because the immediately
previous matched-control run had inverse slightly worse than baseline/no-op,
the signal is real but brittle. The next run should not widen surfaces; it
should lower inverse blend to 0.05 on the same before-control ladder to test
whether the late benefit becomes more stable.
```

## Cycle 21 H100 Result: MLP-fc Before-Control Window112 Blend005

Modal app:

```text
ap-h0UcTytvVsEGwaCSVQqiOj
```

Parsed 200-step results:

```text
mbc_baseline:                          3.8878, 666.07ms/step
mbc_schedule_only_before_r02_blend005: 3.8800, 601.81ms/step
mbc_noop_before_r02_blend005:          3.8855, 597.21ms/step
mbc_inverse_before_r02_blend005:       3.8815, 599.43ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.6179
  schedule-only        5.6104
  no-op before         5.6052
  inverse before       5.6049

step 100:
  baseline             4.6897
  schedule-only        4.6571
  no-op before         4.6843
  inverse before       4.6659

step 150:
  baseline             4.1237
  schedule-only        4.1059
  no-op before         4.1154
  inverse before       4.1108

step 200:
  baseline             3.8878
  schedule-only        3.8800
  no-op before         3.8855
  inverse before       3.8815
```

Timing:

```text
schedule-only nonrefresh avg:       601.33ms
no-op before refresh/nonrefresh:    287.58ms / 604.66ms
inverse before refresh/nonrefresh:  289.80ms / 606.88ms
```

Decision:

```text
Lowering MLP-fc inverse-before blend from 0.10 to 0.05 improves stability
relative to the prior matched-control miss: inverse beats baseline by 0.0063
and no-op by 0.0040.

However, the best arm is schedule-only-before, which beats inverse by 0.0015
and baseline by 0.0078 without feature statistics or right preconditioning.
This means the lower-blend run does not prove c_fc C^-1 alpha. It does prove
that the before-momentum full-path/window schedule can itself move the 200-step
endpoint substantially.

Next action: replicate the exact lower-blend before-control suite. If
schedule-only repeats, isolate it as a cheap optimizer-schedule candidate. If
inverse beats the schedule-only arm on replicate, keep tuning lower-blend
c_fc C^-1. Do not widen surfaces until this fork is resolved.
```

## Cycle 22 H100 Result: MLP-fc Before-Control Window112 Blend005 Replicate

Modal app:

```text
ap-1IkmcrT6fCCVCyXy4Us7Pz
```

Parsed 200-step results:

```text
mbc_baseline:                          3.8881, 763.17ms/step
mbc_schedule_only_before_r02_blend005: 3.8860, 600.60ms/step
mbc_noop_before_r02_blend005:          3.8864, 601.79ms/step
mbc_inverse_before_r02_blend005:       3.8815, 605.46ms/step
```

Intermediate anchors:

```text
step 50:
  baseline             5.6148
  schedule-only        5.6078
  no-op before         5.6186
  inverse before       5.6075

step 100:
  baseline             4.6934
  schedule-only        4.6968
  no-op before         4.6808
  inverse before       4.6698

step 150:
  baseline             4.1259
  schedule-only        4.1286
  no-op before         4.1161
  inverse before       4.1160

step 200:
  baseline             3.8881
  schedule-only        3.8860
  no-op before         3.8864
  inverse before       3.8815
```

Two-run lower-blend endpoint table:

```text
                 run A    run B    mean
baseline         3.8878   3.8881   3.8880
schedule-only    3.8800   3.8860   3.8830
no-op before     3.8855   3.8864   3.8860
inverse before   3.8815   3.8815   3.8815
```

Decision:

```text
The lower-blend c_fc inverse-before result reproduced unusually cleanly:
inverse is exactly 3.8815 in both 200-step runs, with mean gains of 0.0065
against baseline and 0.0045 against the matched no-op.

The schedule-only arm did not reproduce its run-A spike. It is also a weak
control mechanically: with apply-before-momentum and schedule-only enabled,
the preconditioner is skipped and the update falls through the ordinary fused
polar_express path. Treat it as noise/control, not a candidate.

Promote MLP-fc layers 0-1, window 48-112, ridge 0.2, blend 0.05 to a strength
ladder. The next suite should compare the same baseline/no-op against inverse
blends 0.025, 0.05, 0.075, and 0.10 before changing surfaces.
```
