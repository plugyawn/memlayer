# Track 3 LocoProp / Newton-Muon Experiments - 2026-05-31

Context:
- Track: `records/track_3_optimization`, 1x H100, 20 FineWeb chunks.
- Runner: `tools/run_track3_newton_muon.sh`.
- Base script: official `20260505_newton_muon/train_gpt_simple_newton_muon.py`.
- Torch: `2.11`.
- cuDNN SDPA disabled in generated script after Modal/Torch 2.11 cuDNN frontend plan failures.

## Provenance Audit

The apparent contradiction between the reproduced `3.85202` 1x LocoProp-M screen and the stopped Prime official-NM+LocoProp-M lane was not an apples-to-apples algorithm comparison:

- The reproduced `3.85202` run used `records/track_3_optimization/train_gpt_simple.py`, generated with `train_steps=500`.
- The previous "official NM reference" table below used the official Newton-Muon source, generated with `train_steps=3000`.
- The stopped Prime official-NM+LocoProp-M lane used the official Newton-Muon source, generated with `train_steps=3300`.
- The PR291 side lane used the PR291 logged source, generated with `train_steps=500`.

Therefore the earlier cross-run deltas against "official NM reference" should be treated as rough orientation only, not as evidence of fading or persistence. Future GPU launches must match at least `(source script, generated train_steps, mbs, nproc, LocoProp-M settings)` before comparing losses. The runner now prints source, generated script, steps, nproc, mbs, and trial-arg mode before launch, and generated scripts print the source path plus train_steps.

## Active Reference

`track3-nm-3000-h100-20260531-r3`

- Mode: `TRACK3_NM_MODE=inverse`.
- App: `ap-70FfWdH8GjpnM5Dcfwop0Q`.
- Log: `.opencode/modal_track3_nm_3000_h100_20260531_r3.launch.log`.
- Stopped by request after covering enough distance; runner exited after step 1155.

Observed validation:

| Step | Val loss |
| ---: | ---: |
| 125 | 4.66220 |
| 250 | 4.11564 |
| 375 | 3.92664 |
| 500 | 3.82270 |
| 625 | 3.75188 |
| 750 | 3.70750 |
| 875 | 3.66553 |
| 1000 | 3.62499 |
| 1125 | 3.59503 |

## Finite-Step LocoProp Filter

`track3-nm-finite-t2-3000-h100-20260531`

- Mode: `TRACK3_NM_MODE=finite`.
- Filter: continuous-time finite LocoProp response, `t=2.0`, `clip=4.0`.
- App: `ap-zU1ZoGI5FdNyAN6vD83BbF`.
- Stopped early after step 625 screen because it was consistently behind inverse.
- Log: `.opencode/modal_track3_nm_finite_t2_3000_h100_20260531.launch.log`.

Observed validation:

| Step | Val loss | Delta vs inverse at same step |
| ---: | ---: | ---: |
| 125 | 4.66793 | +0.00573 |
| 250 | 4.11702 | +0.00138 |
| 375 | 3.93199 | +0.00535 |
| 500 | 3.82562 | +0.00292 |
| 625 | 3.75684 | +0.00496 |

Read: finite `t=2` did not improve on exact inverse. It stayed near the reference, so the implementation is not obviously broken, but it is not the better Track 3 lever at this setting.

## Additive LocoProp Correction

`track3-nm-additive-t2-a005-3000-h100-20260531`

- Mode: `TRACK3_NM_MODE=additive`.
- Filter: same finite response, `t=2.0`, `clip=4.0`.
- Separate correction alpha: `0.05`.
- App: `ap-au8YjkfAxboXTxJY5ZlgYW`.
- Stopped after first validation screen.
- Log: `.opencode/modal_track3_nm_additive_t2_a005_3000_h100_20260531.launch.log`.

Observed validation:

| Step | Val loss | Delta vs inverse |
| ---: | ---: | ---: |
| 125 | 4.71964 | +0.05744 |

`track3-nm-additive-t2-a0005-3000-h100-20260531`

- Mode: `TRACK3_NM_MODE=additive`.
- Filter: same finite response, `t=2.0`, `clip=4.0`.
- Separate correction alpha: `0.005`.
- App: `ap-xpENbmQD3Lzr3R7JqRmtlV`.
- Stopped after first validation screen.
- Log: `.opencode/modal_track3_nm_additive_t2_a0005_3000_h100_20260531.launch.log`.

Observed validation:

| Step | Val loss | Delta vs inverse |
| ---: | ---: | ---: |
| 125 | 4.68139 | +0.01919 |

Read: additive local displacement on top of Muon/NM state was harmful at both tested scales. Alpha `0.005` was less destructive than `0.05`, but still too far behind to justify continuing.

## Sampled LocoProp-M Local Matching Correction

Implementation:

- Branch/base: local `codex/wr-fresh-20260526`; generated from the official Track 3 `records/track_3_optimization/train_gpt_simple.py`, not from a GitHub PR.
- Files: `tools/make_track3_locoprop_m.py`, `tools/run_track3_locoprop_m.sh`.
- Surface: all 12 MLP `fc` matrices.
- Semantics: leave Muon state unchanged, run a sampled local LocoProp-M matching solve from cached `X`, post-ReLU-squared activations, and preactivation gradients, then apply the local displacement after the Muon step.
- Matching target: `post_target = post - gamma * dpre`.
- Local solve: 4 matching-loss steps, `sample_tokens=1024`, `inner_lr=0.1`, `prox=0.1`, `gamma=1.0`.
- Application: correction is capped at `0.20 * ||Muon update||` per matrix; no norm-to-base rescale.
- Runtime accommodation: `TRACK3_MBS=16` and no `model.compile`, because eager hooks plus `mbs=64` OOM on H100.

Failed smoke:

`track3-locom-m-all-k4-500-h100-20260531`

- App: `ap-Tby3R4S4tYlsd2bsJPTp7O`.
- Log: `.opencode/modal_track3_locom_m_all_k4_500_h100_20260531.launch.log`.
- Result: OOM before the first optimizer step with `mbs=64`.

Active 500-step run:

`track3-locom-m-all-k4-mbs16-500-h100-20260531`

- App: `ap-ls756LDL1iUPDbUPFRY0mI`.
- Log: `.opencode/modal_track3_locom_m_all_k4_mbs16_500_h100_20260531.launch.log`.
- Return code: 0.

Observed validation:

| Step | Val loss | Delta vs official NM reference |
| ---: | ---: | ---: |
| 125 | 4.63912 | -0.02308 |
| 250 | 4.07139 | -0.04425 |
| 375 | 3.85413 | -0.07251 |
| 500 | 3.74983 | -0.07287 |

Timing:

| Step | Step avg |
| ---: | ---: |
| 125 | 3719.22ms |
| 250 | 3600.28ms |
| 375 | 3601.51ms |
| 500 | 3601.85ms |

Diagnostics:

- The loss signal is large versus the previous official-NM reference, especially by 375/500.
- The implementation is not speed-relevant yet: eager mode plus 12 sampled local solves makes it roughly `3.6s/step`.
- The local solver is not cleanly tuned. `lossK` often exceeds `loss0`, sometimes by orders of magnitude, and the correction is frequently governed by the `0.20 * ||Muon update||` cap.
- The sampled correction cosine with raw descent is weak and sometimes negative, so this result should be read as "capped LocoProp-M displacement can move Track 3 strongly," not as evidence that `inner_lr=0.1` is the right local optimizer.
- Same-path alpha-zero control is required because this run changed compile/microbatch/capture behavior relative to the official NM reference.
- Important capture caveat discovered after the initial 1x/8x mismatch: by default the implementation overwrites cached feature/target samples on every microbatch, so the local solve sees only the final microbatch, not the full optimizer batch. This is now explicit as the default "last microbatch" mode.
- Added `TRACK3_LOCOM_ACCUM_SAMPLES=1` and `TRACK3_LOCOM_MICRO_SAMPLE_TOKENS` to test a faithful accumulated-sample variant. With `mbs=16`, `MICRO_SAMPLE_TOKENS=32` gives 1024 total rows on 1x and 1024 gathered rows on 8x.

Alpha-zero control:

`track3-locom-m-all-k4-mbs16-a0-control-500-h100-20260531`

- App: `ap-q9Y06l7o92OcaeQeg9XOeP`.
- Log: `.opencode/modal_track3_locom_m_all_k4_mbs16_a0_control_500_h100_20260531.launch.log`.
- Purpose: identical capture/local-solve path with `TRACK3_LOCOM_ALPHA=0.0`, to separate the LocoProp-M displacement from eager/mbs/local-compute path effects.
- Status: local Modal client/app stopped around step 166, so this did not complete 500.
- First comparable screen: step 125 val `4.68004`.
- Read: at step 125 the active LocoProp-M run beat this same-path alpha-zero control by about `0.0409` loss.

Corrected-owner 1x confirmation:

`track3-locom-m-all-k4-mbs16-500-confirm-r2-h100-20260531`

- App: `ap-8ckZBjRYnwQp8GIaZMcZ1M`.
- Log: `.opencode/modal_track3_locom_m_all_k4_mbs16_500_confirm_r2_h100_20260531.launch.log`.
- Purpose: confirm the 1x signal after the owner-step application path was corrected for distributed compatibility.
- Status: running.

Observed validation:

| Step | Val loss | Delta vs first active LocoProp-M | Delta vs alpha-zero control |
| ---: | ---: | ---: | ---: |
| 125 | 4.64379 | +0.00467 | -0.03625 |
| 250 | 4.07186 | +0.00047 | n/a |
| 375 | 3.85202 | -0.00211 | n/a |
| 450 | 3.77372 | -0.00139 | n/a |
| 475 | 3.75684 | -0.00124 | n/a |
| 500 | 3.74855 | -0.00128 | n/a |

Read: the 1x signal reproduces closely enough after the owner-step correction for this exact 500-step generated run. This should not be compared directly to a 3300-step official Newton-Muon run; the generated script replaces `train_steps` and therefore changes the schedule.

8x H100 distributed tests:

`track3-locom-m-all-k4-8xh100-mbs16-smoke20-20260531`

- App: `ap-wOSZ0i23gRX70iOqVAO12B`.
- Log: `.opencode/modal_track3_locom_m_all_k4_8xh100_mbs16_smoke20_20260531.launch.log`.
- Result: passed 20 steps with `mbs=16`; step 20 val `6.18299`, step avg `479.02ms`.

`track3-locom-m-all-k4-8xh100-mbs16-target328-r1-20260531`

- App: `ap-3vQFqAHx6xAuGtZfU3d1GV`.
- Log: `.opencode/modal_track3_locom_m_all_k4_8xh100_mbs16_target328_r1_20260531.launch.log`.
- Setting: gather sampled local-solve rows across ranks, total `sample_tokens=1024`.
- Status: completed.

Observed validation:

| Step | Val loss |
| ---: | ---: |
| 125 | 4.65208 |
| 250 | 4.10883 |
| 375 | 3.92628 |
| 500 | 3.82689 |
| 625 | 3.75912 |
| 750 | 3.71309 |
| 875 | 3.67272 |
| 1000 | 3.63810 |
| 1125 | 3.61087 |
| 1250 | 3.58144 |
| 1375 | 3.55518 |
| 1500 | 3.52545 |
| 1625 | 3.50672 |
| 1750 | 3.48503 |
| 1875 | 3.46570 |
| 2000 | 3.44620 |
| 2125 | 3.42888 |
| 2250 | 3.41089 |
| 2375 | 3.39460 |
| 2500 | 3.37829 |
| 2625 | 3.36138 |
| 2750 | 3.34522 |
| 2875 | 3.32902 |
| 3000 | 3.31322 |
| 3025 | 3.30928 |
| 3050 | 3.30617 |
| 3075 | 3.30343 |
| 3100 | 3.30059 |
| 3125 | 3.29779 |
| 3150 | 3.29479 |
| 3175 | 3.29221 |
| 3200 | 3.28959 |
| 3225 | 3.28724 |
| 3250 | 3.28515 |
| 3275 | 3.28334 |
| 3300 | 3.28177 |
| 3325 | 3.28059 |
| 3350 | 3.28003 |

Read: the 8x gathered path is much faster, but it does not reproduce the strong 1x 500-step loss. It still essentially reaches the Track 3 target distance, ending at `3.28003` after 3350 steps with final validation step avg `488.81ms`. This may be because cross-rank sample aggregation changes/cancels the local matching correction; the correction diagnostics show small or unstable cosine with raw descent on some owner layers.

Queued batching diagnostic:

`track3-locom-m-all-k4-8xh100-mbs16-nogather-local1024-500-r1-20260531`

- App: `ap-Er7gnOFDojDlp4lp3SuDuR`.
- Log: `.opencode/modal_track3_locom_m_all_k4_8xh100_mbs16_nogather_local1024_500_r1_20260531.launch.log`.
- Setting: `TRACK3_LOCOM_GATHER_SAMPLES=0`, `TRACK3_LOCOM_SAMPLE_TOKENS=1024`; each owning rank solves from its local 1024-row sample rather than a cross-rank gathered sample.
- Purpose: directly test whether the distributed/global sample construction is washing out the early 1x signal.
- Status: created/queued, no training output yet.

Queued accumulated-sample diagnostic:

`track3-locom-m-all-k4-mbs16-accum32-125-h100-r1-20260531`

- App: pending in `.opencode/modal_track3_locom_m_all_k4_mbs16_accum32_125_h100_r1_20260531.launch.log`.
- Setting: `TRACK3_LOCOM_ACCUM_SAMPLES=1`, `TRACK3_LOCOM_MICRO_SAMPLE_TOKENS=32`, 1x H100, 125 steps.
- Purpose: test whether the strong 1x last-microbatch signal survives when the local LocoProp-M solve sees samples accumulated across all microbatches in the optimizer step.
- Status: failed before step 1 with CUDA OOM. The eager hook path plus accumulated samples used about `75.7 GiB` allocated and failed on an additional `3.07 GiB` allocation. Accumulated sampling needs a streaming/compact implementation before it is viable.

## Current WR `train_gpt.py` LocoProp-M Side Run

`wr-locom-m-cfc-k4-mbs-default-500-h100-r1-20260531`

- App: pending in `.opencode/modal_wr_locom_m_cfc_k4_500_h100_r1_20260531.launch.log`.
- Runner: `tools/run_wr_locoprop_m_500.sh`.
- Generator: `tools/make_wr_locoprop_m.py`.
- Surface: current WR `mlp_bank[:, 0]` / MLP `c_fc` only.
- Setting: 1x H100, 500 steps, `WR_LOCOM_STEPS=4`, `WR_LOCOM_SAMPLE_TOKENS=1024`, `WR_LOCOM_INNER_LR=0.1`, `WR_LOCOM_PROX=0.1`, `WR_LOCOM_NORM_CAP=0.20`.
- Semantics: same sampled LocoProp-M local matching correction as Track 3, applied as a state-decoupled post-NorMuon displacement through the WR bank update machinery.
- Status: launched by mistake after misunderstanding "Track 3 WR"; local Modal client was stopped. Do not use this as evidence for the Track 3 question.

## Track 3 Newton-Muon WR + LocoProp-M

`track3-nm-locom-m-all-k4-mbs16-500-h100-r1-20260531`

- App: `ap-0hClpIUHRTyqF0xxTenp9e`.
- Log: `.opencode/modal_track3_nm_locom_m_all_k4_mbs16_500_h100_r1_20260531.launch.log`.
- Runner: `tools/run_track3_locoprop_m.sh`.
- Source: `records/track_3_optimization/results/20260505_newton_muon/train_gpt_simple_newton_muon.py`.
- Setting: official Track 3 Newton-Muon script plus sampled LocoProp-M over all MLP `fc` surfaces, 1x H100, 500 steps, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, cap `0.20`.
- Status: launched/created, no training values yet.

## Prime Track 3 Newton-Muon + LocoProp-M

`track3_nm_locom_k4_mbs16_4xh100_target328_pair_r2_20260531`

- Provider: Prime Intellect.
- Pod: `d60c61dbd5284331b6467023e35acf9c`, `4x H100 PCIe`, `$9.40/hr`.
- Source: official Track 3 Newton-Muon script, `records/track_3_optimization/results/20260505_newton_muon/train_gpt_simple_newton_muon.py`.
- Setting: `NPROC_PER_NODE=4`, two trials to target `3.28`, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, gathered samples, cap `0.20`.
- Status: terminated after the step-375 screen because the distributed curve still did not match the reproduced 1x LocoProp-M signal.

Observed validation:

| Step | Val loss |
| ---: | ---: |
| 125 | 4.56972 |
| 250 | 4.09108 |
| 375 | 3.90836 |

Read: early step 125 was strong, but by 375 it lagged the reproduced corrected 1x LocoProp-M screen (`3.85202`) by about `0.056`. Per user instruction, the 4x lane was killed rather than spending into a distributed mismatch.

`track3_nm_locom_k4_mbs16_1xh100_target328_pair_r2_20260531`

- Provider: Prime Intellect.
- Pod: `b45df3092c7640cf9f7b112cb54534f0`, `1x H100 PCIe`, `$2.35/hr`.
- Same source/settings as above, except `NPROC_PER_NODE=1`.
- Status: still running toward the requested 1x benchmark/target-loss evidence.

Observed validation so far:

| Step | Val loss |
| ---: | ---: |
| 125 | 4.56482 |
| 250 | 4.09889 |

Read: this was stopped after the provenance mismatch audit. It used the official Newton-Muon source and `train_steps=3300`, while the reproduced `3.85202` LocoProp-M signal used the simple base Track 3 source and `train_steps=500`. The apparent fade comparison was therefore not apples-to-apples. Within this stopped 3300-step official-NM lane, the step-125 gap versus the previous official-NM reference was large (`4.66220 - 4.56482 = 0.09738`) but had narrowed by step 250 (`4.11564 - 4.09889 = 0.01675`).

## Modal Track 3 Current-Lowest PR291 + LocoProp-M

`track3-pr291-locom-m-k4-mbs16-500-h100-r1-20260531`

- Provider: Modal, H100.
- App: `ap-j27eGyVv18nPJLmFGBRnjb`.
- Source: current lowest-steps Track 3 path, `records/track_3_optimization/results/20260509_contra_soft_muon/f6d6db35-7565-42da-a4d5-57f3b032a90b.txt`.
- Setting: generated LocoProp-M over all MLP `fc` surfaces, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, cap `0.20`, 500-step screen.
- Status: failed before training because PR291 uses argparse and rejects the old positional trial argument.
- Log: `.opencode/modal_track3_pr291_locom_m_k4_mbs16_500_h100_r1_20260531.launch.log`.

`track3-pr291-locom-m-k4-mbs16-500-h100-r1b-20260531`

- Provider: Modal, H100.
- App: `ap-pyWiiZoCpXa1JdwaVhjKOy`.
- Same source/settings as above, with `TRACK3_PASS_TRIAL_ARG=0`.
- Status: stopped during the provenance mismatch audit. LocoProp-M hooks fired at steps 0, 1, and 2; step 2 applied nonzero capped corrections. Step 125 validation was `4.50059` at `4164.89ms/step`, which is basically in the PR291 baseline band rather than a clear early LocoProp-M win.
- Latest diagnostics: step 50 hooks are active on all owned MLP `fc` surfaces. Corrections are nonzero and capped; several early raw local solves are unstable, but by step 50 the observed first-layer correction scale is around `1.17e-02` and the first four logged `cos_desc` values are small/negative (`-0.034`, `-0.075`, `-0.035`, `-0.023`), so the first validation screen is the real decision point.
- Log: `.opencode/modal_track3_pr291_locom_m_k4_mbs16_500_h100_r1b_20260531.launch.log`.
