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
