# Newton-V Modal Experiment Results - 2026-05-27

Branch: `codex/wr-fresh-20260526`

Raw logs:

- `.opencode/modal_newtonv_quick_h100_20260527.log`
- `.opencode/modal_newtonv_promote_h100_20260527.log`

Runner returned `gpu: H100`, `returncode: 0` for the promotion suite. The
earlier quick suite was launched before the runner default was changed away
from `H100!`, so use its timing as a same-session screen, not a clean pricing
artifact.

## Quick Suite

Command shape:

```bash
NANOGPT_MODAL_GPU=H100 \
MODAL_RUNNER=tools/run_newtonv_experiment_suite.sh \
SCREEN_STEPS=80 SCREEN_VAL_EVERY=20 \
tools/run_modal_newtonv_raw_gate.sh
```

Parsed results:

| case | final_step | final_val_loss | final_train_time_s | final_step_avg_ms | refresh_step_ms_avg | nonrefresh_step_ms_avg | peak_alloc_mib |
| --- | --- | --- | --- | --- | --- | --- | --- |
| timing_baseline | 80 | 4.5380 | 36.059 | 450.74 |  | 449.54 | 37326 |
| timing_noop | 80 | 4.5231 | 36.155 | 451.94 | 425.88 | 453.12 | 37430 |
| timing_active_inverse | 80 | 4.5186 | 36.265 | 453.32 | 427.00 | 454.51 | 37430 |
| block_power_a075 | 80 | 4.5315 | 37.317 | 466.46 | 585.25 | 453.75 | 37353 |
| block_power_a050 | 80 | 4.5361 | 37.348 | 466.85 | 583.12 | 454.38 | 37353 |
| block_power_shrink_only | 80 | 4.5484 | 37.336 | 466.70 | 581.81 | 454.33 | 37353 |
| block_finite_t2 | 80 | 4.5338 | 37.288 | 466.10 | 581.57 | 453.69 | 37353 |

Read:

- The dense inverse path still gives the best short-screen loss:
  `4.5186` vs `4.5380` baseline at 80 steps.
- The no-op control was also better than baseline at 80 steps, so the short
  screen is not by itself enough evidence for WR promotion.
- The block/power/finite filters did not preserve the inverse signal and added
  refresh overhead. `shrink_only` was worse than baseline, which argues against
  "dominant eigenspace shrink alone" as the whole mechanism.

## Promotion Suite

Command shape:

```bash
NANOGPT_MODAL_GPU=H100 \
MODAL_RUNNER=tools/run_newtonv_experiment_suite.sh \
MODAL_EXTRA_ENV_JSON='{"NEWTONV_SUITE":"promote","NEWTONV_SUITE_LABEL":"modal_promote_h100_20260527"}' \
SCREEN_STEPS=200 SCREEN_VAL_EVERY=50 \
tools/run_modal_newtonv_raw_gate.sh
```

Parsed results:

| case | final_step | final_val_loss | final_train_time_s | final_step_avg_ms | refresh_step_ms_avg | nonrefresh_step_ms_avg | peak_alloc_mib |
| --- | --- | --- | --- | --- | --- | --- | --- |
| promote_baseline | 200 | 3.8837 | 283.590 | 1417.95 |  | 1417.52 | 37327 |
| promote_active_inverse_all_win48 | 200 | 3.8954 | 123.203 | 616.02 | 309.10 | 626.66 | 37430 |
| promote_raw_v01_end100 | 200 | 3.8875 | 215.057 | 1075.29 | 7531.70 | 625.93 | 37430 |

Validation-loss checkpoints:

| case | step 50 | step 100 | step 150 | step 200 |
| --- | --- | --- | --- | --- |
| promote_baseline | 5.6052 | 4.6861 | 4.1150 | 3.8837 |
| promote_active_inverse_all_win48 | 5.5893 | 4.6956 | 4.1265 | 3.8954 |
| promote_raw_v01_end100 | 5.5970 | 4.6782 | 4.1145 | 3.8875 |

Read:

- `promote_active_inverse_all_win48` had the familiar early gain at step 50 but
  was already behind baseline by step 100 and finished worse by `+0.0117`.
- `promote_raw_v01_end100` was better at steps 50 and 100, tied by step 150,
  and finished worse by `+0.0038`.
- The promotion baseline had major compile spikes, so its wall-clock is not a
  clean final timing reference. The loss comparison is the important output:
  the current Newton-V candidates did not persist to 200 steps.

## Decision

Do not promote the current Newton-V inverse or block-filter configurations to a
WR attempt.

The right-side feature axis is still not disproven: the short-screen signal is
real enough to explain why this looked promising. But the 200-step loss gates
say the current schedules and filters are not record candidates. Further H100
time should not go into broad V-filter sweeps unless we change the interaction
with the existing NorMuon/Polar stack.

The only follow-up that looks principled enough to justify more GPU is a small
overpreconditioning test: turn down or gate the existing Muon/NorMuon
normalization on V while the right-side feature preconditioner is active. That
tests whether `polar(M C^-1)` is currently fighting a tuned update scale or
directional regularizer. Everything else should wait.

## Tight Permutation Queue

If we spend one more small H100 window before implementing a new NorMuon
downtune knob, keep it to the permutations that can still answer a question:

| case | purpose |
| --- | --- |
| `V all, window 0-48, POLAR_ITERS=4` | highest-priority direct test of 4-iter Polar with dense inverse Newton-V |
| `V 0-1, END_STEP=100, POLAR_ITERS=4` | highest-priority direct test on the early-layer pulse candidate |
| `V 0-1, window 0-48` | separate early pulse from the current `END_STEP=100` fade |
| `V 0-1, window 0-64` | check whether the useful pulse lasts slightly past the 60-step hit |
| `qk` only, window `0-48` | surface control for the attention-input Gram |
| `o` only, window `0-48` | output-feature control, only if the first four are not dead |

Run these only as 80-step screens first. Promote nothing unless it beats the
80-step baseline and the no-op control by a clear margin; the 200-step promotion
suite showed that a pretty early loss is not enough.

Highest-priority prepared runner:

```bash
NANOGPT_MODAL_GPU=H100 \
MODAL_RUNNER=tools/run_newtonv_experiment_suite.sh \
MODAL_EXTRA_ENV_JSON='{"NEWTONV_SUITE":"polar4","NEWTONV_SUITE_LABEL":"modal_polar4_h100"}' \
PERM_STEPS=80 PERM_VAL_EVERY=20 \
tools/run_modal_newtonv_raw_gate.sh
```

Full permutation runner, only if the two `polar4` cases stay alive:

```bash
NANOGPT_MODAL_GPU=H100 \
MODAL_RUNNER=tools/run_newtonv_experiment_suite.sh \
MODAL_EXTRA_ENV_JSON='{"NEWTONV_SUITE":"permutations","NEWTONV_SUITE_LABEL":"modal_permutations_h100"}' \
PERM_STEPS=80 PERM_VAL_EVERY=20 \
tools/run_modal_newtonv_raw_gate.sh
```

## Next Ladder

The next paid H100 run should test the two highest-priority suspicions at once:

- `POLAR_ITERS=4` may be the less overpreconditioned Newton-V partner.
- Starting Newton-V at step 0 may be wrong because attention inputs and
  optimizer state are still in their init/warmup regime.

Prepared suite:

```bash
NANOGPT_MODAL_GPU=H100 \
MODAL_RUNNER=tools/run_newtonv_experiment_suite.sh \
MODAL_EXTRA_ENV_JSON='{"NEWTONV_SUITE":"next","NEWTONV_SUITE_LABEL":"modal_next_h100"}' \
NEXT_STEPS=120 NEXT_VAL_EVERY=40 \
tools/run_modal_newtonv_raw_gate.sh
```

Cases, in order:

| case | purpose |
| --- | --- |
| `next_baseline` | same-suite 120-step baseline |
| `next_noop_vall_win32_80_p4` | full-path/no-op control for delayed 4-iter window |
| `next_polar4_vall_win0_48` | clean 4-iter compare against prior all-layer V window |
| `next_polar4_v01_end100` | clean 4-iter compare against prior early-layer end-step candidate |
| `next_polar4_vall_win32_80` | delayed all-layer V |
| `next_polar4_v01_win32_80` | delayed early-layer V |
| `next_polar4_v01_win48_112` | later early-layer V pulse |
| `next_qk_win32_80_p4` | delayed QK-only surface control |
| `next_o_win32_80_p4` | delayed O-only headwise surface control |

If the `next` suite is interrupted after the V cases, resume only the remaining
tail:

```bash
NANOGPT_MODAL_GPU=H100 \
MODAL_RUNNER=tools/run_newtonv_experiment_suite.sh \
MODAL_EXTRA_ENV_JSON='{"NEWTONV_SUITE":"tail","NEWTONV_SUITE_LABEL":"modal_tail_h100"}' \
NEXT_STEPS=120 NEXT_VAL_EVERY=40 \
tools/run_modal_newtonv_raw_gate.sh
```

## Next Ladder Results

Logs:

- `.opencode/modal_newtonv_next_h100_20260527.partial.log`
- `.opencode/modal_newtonv_tail_h100_20260527.log`

The first Modal app hit a local client `StreamTerminatedError` after completing
six cases and while starting `next_polar4_v01_win48_112`. The app canceled that
input, so the remaining three cases were resumed with `NEWTONV_SUITE=tail`.
The tail app completed cleanly on `gpu: H100`.

Parsed final results:

| case | final_step | final_val_loss | final_train_time_s | final_step_avg_ms | refresh_step_ms_avg | nonrefresh_step_ms_avg | peak_alloc_mib |
| --- | --- | --- | --- | --- | --- | --- | --- |
| next_baseline | 120 | 4.1813 | 69.741 | 581.17 |  | 580.38 | 37327 |
| next_noop_vall_win32_80_p4 | 120 | 4.1891 | 171.033 | 1425.27 | 15067.43 | 579.35 | 37430 |
| next_polar4_vall_win0_48 | 120 | 4.1923 | 70.622 | 588.51 | 376.22 | 600.82 | 37430 |
| next_polar4_v01_end100 | 120 | 4.1908 | 149.671 | 1247.26 | 6664.35 | 588.22 | 37430 |
| next_polar4_vall_win32_80 | 120 | 4.1906 | 102.471 | 853.93 | 5220.11 | 582.62 | 37430 |
| next_polar4_v01_win32_80 | 120 | 4.1864 | 101.545 | 846.21 | 5108.42 | 581.34 | 37430 |
| tail_polar4_v01_win48_112 | 120 | 4.1793 | 210.721 | 1756.01 | 9361.59 | 1138.17 | 37430 |
| tail_qk_win32_80_p4 | 120 | 4.1874 | 238.240 | 1985.33 | 22448.61 | 716.53 | 37430 |
| tail_o_win32_80_p4 | 120 | 4.1809 | 237.527 | 1979.39 | 22378.15 | 714.57 | 37343 |

Validation checkpoints:

| case | step 40 | step 80 | step 120 |
| --- | --- | --- | --- |
| next_baseline | 5.8338 | 4.6195 | 4.1813 |
| next_noop_vall_win32_80_p4 | 5.8441 | 4.6350 | 4.1891 |
| next_polar4_vall_win0_48 | 5.8222 | 4.6360 | 4.1923 |
| next_polar4_v01_end100 | 5.8439 | 4.6442 | 4.1908 |
| next_polar4_vall_win32_80 | 5.8353 | 4.6300 | 4.1906 |
| next_polar4_v01_win32_80 | 5.8570 | 4.6307 | 4.1864 |
| tail_polar4_v01_win48_112 | 5.8293 | 4.6159 | 4.1793 |
| tail_qk_win32_80_p4 | 5.8314 | 4.6202 | 4.1874 |
| tail_o_win32_80_p4 | 5.8360 | 4.6115 | 4.1809 |

Read:

- `POLAR_ITERS=4` is not a general fix. The direct comparisons are worse:
  all-layer `0-48` finished `4.1923`; early-layer `END_STEP=100` finished
  `4.1908`.
- Delaying V helps only when the pulse is late enough. `V 0-1, 32-80` finished
  `4.1864`, still worse; `V 0-1, 48-112` finished `4.1793`, a small
  `-0.0020` loss gain at step 120.
- QK-only delayed is not promising here: `4.1874` final, worse than baseline.
- O headwise delayed is a real short-screen hit and barely persists:
  `4.6115` at step 80 and `4.1809` at step 120, a small `-0.0004` final gain.
- The implementation is too slow for WR. The positive `V 48-112` and O cases
  had huge compile/refresh overhead in this 1x Modal setup.

The important theory update is that step-zero activation was likely wrong. The
best V result in this ladder was a later pulse, not the initial window. Also,
O headwise is now a better surface than QK for follow-up, but the effect fades
substantially by step 120.

Next useful code change:

```text
Collect feature Grams before apply windows.
```

Current delayed windows start collection and application together; the EMA is
zero before the window opens. A better test is:

```text
collect: 0-48 or 0-64
apply:   48-112
```

That would test the actual init-aware hypothesis: warm the metric during early
training, but do not perturb V/O until the attention path is less transient.

## Warm-Metric Ladder Results

Log:

- `.opencode/modal_newtonv_warmmetric_h100_20260527.log`

Timing/accounting:

- Modal app: `ap-sSL50qhWTRJ3JKcQBp5FJ3`
- GPU: `H100`
- Launched around `2026-05-27 17:00 IST`.
- Completed around `2026-05-27 17:24 IST`.
- Modal-reported wall time: `1402.985s`.
- Return code: `0`.

This run tested the decoupled-window hypothesis:

```text
collect feature Gram early
apply Newton-Muon preconditioner later
```

Parsed final results:

| case | final_step | final_val_loss | final_train_time_s | final_step_avg_ms | refresh_step_ms_avg | nonrefresh_step_ms_avg | peak_alloc_mib |
| --- | --- | --- | --- | --- | --- | --- | --- |
| warm_baseline | 120 | 4.1832 | 103.940 | 866.13 |  | 865.33 | 37327 |
| warm_v01_collect0_48_apply48_112_p4 | 120 | 4.1829 | 67.632 | 563.60 | 348.87 | 576.06 | 37430 |
| warm_v01_collect0_64_apply48_112_p4 | 120 | 4.1846 | 66.922 | 557.68 | 385.01 | 570.82 | 37430 |
| warm_o_collect0_64_apply48_112_p4 | 120 | 4.1861 | 67.746 | 564.55 | 455.19 | 572.55 | 37343 |
| warm_vo_collect0_64_apply48_112_p4 | 120 | 4.1847 | 66.976 | 558.13 | 405.43 | 569.65 | 37447 |

Validation checkpoints:

| case | step 0 | step 40 | step 80 | step 120 |
| --- | --- | --- | --- | --- |
| warm_baseline | 10.8319 | 5.8510 | 4.6326 | 4.1832 |
| warm_v01_collect0_48_apply48_112_p4 | 10.8335 | 5.8165 | 4.6256 | 4.1829 |
| warm_v01_collect0_64_apply48_112_p4 | 10.8286 | 5.8323 | 4.6282 | 4.1846 |
| warm_o_collect0_64_apply48_112_p4 | 10.8260 | 5.8174 | 4.6339 | 4.1861 |
| warm_vo_collect0_64_apply48_112_p4 | 10.8283 | 5.8587 | 4.6248 | 4.1847 |

Read:

- The implementation worked: delayed runs now populate Gram EMA before the apply
  window instead of starting from a cold metric at step 48.
- No warm-metric candidate cleared the promotion bar. The best final result was
  `V 0-1 collect 0-48 / apply 48-112`, `4.1829` versus baseline `4.1832`, only
  a `0.0003` gain.
- `collect 0-64` was worse than `collect 0-48`, suggesting later/higher-energy
  V statistics are not automatically better.
- Warm O did not reproduce the prior O delayed hit. It finished `4.1861`,
  clearly worse than baseline.
- Combined V+O had the best step-80 value, `4.6248`, but faded to `4.1847`.

The current read is that warm feature metrics can move early loss, but the
effect is still not persistent enough by step 120. This demotes collect/apply
windowing as a mainline WR path by itself.

Next ladder:

```text
baseline
warm V no-op/full-path control
warm V polar5
warm V polar4
warm V polar4 with LOCO_FULL_SKIP_VARRED=1
```

This tests whether the right-side V metric is being over-normalized by the
existing Polar/NorMuon variance-reduction stack. Commit `62e7097` added the
`LOCO_FULL_SKIP_VARRED` knob and an `overprecond` suite for that purpose.

## Overpreconditioning Ladder Results

Log:

- `.opencode/modal_newtonv_overprecond_h100_20260527.log`

Timing/accounting:

- Modal app: `ap-9WOCEPdPIu5SZKslqZsOtb`
- GPU: `H100`
- Launched around `2026-05-27 17:28 IST`.
- Completed around `2026-05-27 17:49 IST`.
- Modal-reported wall time: `1217.204s`.
- Return code: `0`.

This run used the remaining GPU-hour allowance after the warm-metric ladder.
Total active H100 window for both Modal apps was about `17:00-17:49 IST`.

Parsed final results:

| case | final_step | final_val_loss | final_train_time_s | final_step_avg_ms | refresh_step_ms_avg | nonrefresh_step_ms_avg | peak_alloc_mib |
| --- | --- | --- | --- | --- | --- | --- | --- |
| over_baseline | 120 | 4.1869 | 72.443 | 603.69 |  | 602.90 | 37327 |
| over_v01_warm_noop_polar4 | 120 | 4.1798 | 72.776 | 606.46 | 421.28 | 620.61 | 37430 |
| over_v01_warm_polar5 | 120 | 4.1821 | 72.512 | 604.26 | 385.64 | 621.13 | 37430 |
| over_v01_warm_polar4 | 120 | 4.1763 | 72.882 | 607.35 | 384.74 | 624.55 | 37430 |
| over_v01_warm_polar4_skipvr | 120 | 4.1784 | 72.765 | 606.38 | 385.80 | 623.40 | 37430 |

Validation checkpoints:

| case | step 0 | step 40 | step 80 | step 120 |
| --- | --- | --- | --- | --- |
| over_baseline | 10.8310 | 5.8303 | 4.6244 | 4.1869 |
| over_v01_warm_noop_polar4 | 10.8283 | 5.8273 | 4.6108 | 4.1798 |
| over_v01_warm_polar5 | 10.8279 | 5.7874 | 4.6183 | 4.1821 |
| over_v01_warm_polar4 | 10.8332 | 5.8336 | 4.6182 | 4.1763 |
| over_v01_warm_polar4_skipvr | 10.8291 | 5.8563 | 4.6192 | 4.1784 |

Read:

- The full-path no-op control is strong: `4.1798` versus baseline `4.1869`.
  This means the no-op/polar4 scheduling path itself is useful in this suite.
- Caveat: this no-op control used the timing-triplet runner default
  `LOCO_DIAG_ATTN_LAYERS=all`, while the active raw V cases used layers `0-1`.
  Treat active-vs-noop as suggestive, not a matched-control result.
- Active Newton-V with polar4 beat both baseline and no-op: `4.1763`, a
  `0.0106` gain versus baseline and a `0.0035` gain versus no-op.
- Active Newton-V with polar5 was worse than no-op: `4.1821`.
- Skipping NorMuon variance reduction was worse than normal polar4:
  `4.1784` versus `4.1763`. The useful variant keeps variance reduction.
- Non-refresh timing overhead is small in this 1xH100 suite: best active
  `607.35ms/step` versus baseline `603.69ms/step`, about `+0.6%`.

Current interpretation:

```text
The right-side V preconditioner only looks useful when paired with the
weaker 4-iteration full-path polar schedule.

The no-op full path is itself a strong confound and may be an independent
optimizer/schedule lever.

Do not skip NorMuon variance reduction.
```

Next GPU-hour gate:

```text
200-step same-suite:
  baseline
  warm V 0-1 no-op polar4
  warm V 0-1 no-op polar5
  warm all-V no-op polar4
  warm V 0-1 active polar5
  warm V active polar4
```

Commit `d5de543` logged the uncorrected overprecond suite; the follow-up patch
sets `LOCO_DIAG_ATTN_LAYERS=0-1` on the no-op controls for future matched runs.
Promote only if active polar4 beats baseline, matched V0-1 no-op polar4, and
matched active/no-op polar5 controls by at least `0.002` at 200 steps. If a
no-op control beats active or active fades, the Newton-specific part should be
demoted and the no-op polar/full-path schedule should become the new branch.

Mechanism note: `LOCO_FULL_NOOP=1` still uses the full after-momentum path
during the apply window; it just passes blend zero to the feature preconditioner.
So the no-op result is not pure overhead. It is a real polar4/full-path schedule
ablation.

## Overpromote 200-Step Matched Control Results

Log:

- `.opencode/modal_newtonv_overpromote_h100_20260527.log`

Timing/accounting:

- Modal app: `ap-g1YDghiIetiBqd6GxM0ATO`
- GPU: `H100`
- Launched around `2026-05-27 18:02 IST`.
- Completed around `2026-05-27 18:25 IST`.
- Modal-reported wall time: `1366.576s`.
- Return code: `0`.

Parsed final results:

| case | final_step | final_val_loss | final_train_time_s | final_step_avg_ms | refresh_step_ms_avg | nonrefresh_step_ms_avg | peak_alloc_mib |
| --- | --- | --- | --- | --- | --- | --- | --- |
| overpromote_baseline | 200 | 3.8882 | 121.823 | 609.12 |  | 608.63 | 37327 |
| overpromote_v01_warm_noop_polar4 | 200 | 3.8918 | 123.243 | 616.22 | 282.01 | 631.47 | 37430 |
| overpromote_v01_warm_noop_polar5 | 200 | 3.8856 | 120.890 | 604.45 | 282.59 | 619.12 | 37430 |
| overpromote_vall_warm_noop_polar4 | 200 | 3.8851 | 120.655 | 603.27 | 309.57 | 616.62 | 37430 |
| overpromote_v01_warm_active_polar5 | 200 | 3.8869 | 120.464 | 602.32 | 280.73 | 616.97 | 37430 |
| overpromote_v01_warm_active_polar4 | 200 | 3.8887 | 120.959 | 604.79 | 279.69 | 619.62 | 37430 |

Validation checkpoints:

| case | step 50 | step 100 | step 150 | step 200 | delta vs baseline @200 |
| --- | ---: | ---: | ---: | ---: | ---: |
| overpromote_baseline | 5.5870 | 4.6961 | 4.1168 | 3.8882 | +0.0000 |
| overpromote_v01_warm_noop_polar4 | 5.6061 | 4.6909 | 4.1338 | 3.8918 | +0.0036 |
| overpromote_v01_warm_noop_polar5 | 5.6231 | 4.6886 | 4.1190 | 3.8856 | -0.0026 |
| overpromote_vall_warm_noop_polar4 | 5.6231 | 4.7031 | 4.1176 | 3.8851 | -0.0031 |
| overpromote_v01_warm_active_polar5 | 5.6301 | 4.6890 | 4.1164 | 3.8869 | -0.0013 |
| overpromote_v01_warm_active_polar4 | 5.6403 | 4.6826 | 4.1220 | 3.8887 | +0.0005 |

Read:

- This demotes Newton-specific V for the current warm-window candidate. Active
  V0-1 polar4 did not beat baseline or the no-op controls at 200 steps.
- The strongest line was the no-op/full-path schedule: all-V no-op polar4
  landed at `3.8851`, a `0.0031` gain versus baseline.
- The winning no-op lines were not uniformly better early. Both strong controls
  were worse at step 50, recovered around steps 100-150, then won by step 200.
  Treat this as an optimizer-trajectory effect, not a simple first-50-step
  acceleration.
- Matched V0-1 no-op polar5 also beat baseline: `3.8856`, a `0.0026` gain.
- Active Newton-V polar5 beat baseline but did not beat the best no-op control:
  `3.8869` versus `3.8851`.
- Active Newton-V polar4 finished worse than baseline: `3.8887` versus
  `3.8882`.
- No-op is still not pure baseline. It routes the selected bank through the
  explicit after-momentum full path with `blend=0`, including the right-inverse
  helper with an identity/zero-effect preconditioner.
- No-op/full-path activation is bank-level. With `LOCO_FULL_SURFACES=v`, the
  whole `vo_bank` goes through the explicit after-momentum path; layer selection
  changes feature collection and identity/preconditioner helper work, not which
  matrices use `polar_express_from_operand`.

Decision:

```text
Do not promote Newton-V from this ladder.
Promote the full-path/no-op schedule to the next isolation ladder.
```

Next isolation target:

```text
Separate the useful optimizer-path change from wasted feature-stat work:
  1. baseline
  2. full-path VO-bank no-op, no feature refresh/collection, polar5
  3. full-path VO-bank no-op, no feature refresh/collection, polar4
  4. current no-op controls with collection enabled for replication
```

Prepared runner:

```text
NEWTONV_SUITE=scheduleonly
```

Implementation note: `LOCO_FULL_SCHEDULE_ONLY=1` now preserves the explicit
VO-bank after-momentum path while disabling feature collection, factor refresh,
right-preconditioner helper calls, and full-stat buffer allocation/zeroing.

Promotion rule:

```text
Promote no-stats schedule-only if:
  final @200 <= baseline - 0.003
  final @200 <= collection-enabled no-op replicate
  non-refresh timing <= baseline * 1.03

Kill no-stats schedule-only if:
  final @200 is within +/-0.002 of baseline or worse
  only collection-enabled no-op variants retain the win
  polar4/polar5 ordering is unstable across same-suite controls
```

If the no-refresh no-op keeps the `~0.002-0.003` gain with near-baseline timing,
it becomes a real WR candidate knob independent of Newton-Muon. If it loses the
gain, the feature-stat side effects or identity right-matmul/norm path are part
of the behavior and need their own narrower ablation.
