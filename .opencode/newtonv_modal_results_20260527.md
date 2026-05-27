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
