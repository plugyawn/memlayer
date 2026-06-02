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

Matched audit after the tooling fix:

`track3-nm500-locom-m-k4-mbs16-active-h100-audit-20260531`

- Provider: Modal, H100.
- App: `ap-n0OpQ93S21q6DKLGYsbN45`.
- Source: official Newton-Muon, `records/track_3_optimization/results/20260505_newton_muon/train_gpt_simple_newton_muon.py`.
- Generated schedule: `train_steps=500`, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, cap `0.20`, `TRACK3_LOCOM_ALPHA=1.0`.
- Log: `.opencode/modal_track3_nm500_locom_m_k4_mbs16_active_h100_audit_20260531.launch.log`.
- Status: stopped after step 250.

`track3-nm500-locom-m-k4-mbs16-alpha0-h100-audit-20260531`

- Provider: Modal, H100.
- App: `ap-ModsFRV41FgbJ7hcQPFC0b`.
- Same source/schedule/settings, except `TRACK3_LOCOM_ALPHA=0.0`.
- Log: `.opencode/modal_track3_nm500_locom_m_k4_mbs16_alpha0_h100_audit_20260531.launch.log`.
- Status: stopped after step 250.

Observed validation:

| Step | Active LocoProp-M | Alpha-zero control | Active delta |
| ---: | ---: | ---: | ---: |
| 125 | 4.56776 | 4.60917 | -0.04141 |
| 250 | 4.08164 | 4.05400 | +0.02764 |

Read: matched provenance restores a real early step-125 LocoProp-M effect, but the current sampled local solve/cap setup flips negative by step 250 under official Newton-Muon. At step 250 one logged active layer has `lossK=1.232e+04`, `corr_norm=6.911e+03`, and `cos_desc=-0.952`, so the local solver is sometimes producing a strongly anti-descent correction that only survives through a tiny norm-cap scale. This points to a solver/correction-quality problem, not a disappearance caused by cross-run schedule mismatch.

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

## Modal Simple Track 3 Base + LocoProp-M Target Runs

`track3-simple-locom-target328-1xh100-laneA-2trials-20260531`

- Provider: Modal, H100.
- App: `ap-vSvCYOO6msUHj4RiSBqw2m`.
- Source: simple Track 3 base, `records/track_3_optimization/train_gpt_simple.py`.
- Setting: 1x H100, two sequential trials, `SCREEN_STEPS=3350`, `TRACK3_TARGET_LOSS=3.28`, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, all MLP `fc` surfaces, cap `0.20`.
- Seeds: trial seeds `0` and `1` via `TRACK3_SEED_BASE=0`, `TRACK3_SEED_OFFSET=0`.
- Status: detached and running. Early log confirms `track3_trial_seed=0 trial=0`, LocoProp-M owner hooks on all 12 MLP `fc` layers, and active capped corrections by step 2. Last launch-log observation reached step 42 with `step_avg=3885.28ms`.
- Log: `.opencode/modal_track3_simple_locom_target328_1xh100_laneA_2trials_20260531.launch.log`.

`track3-simple-locom-target328-1xh100-laneB-2trials-20260531`

- Provider: Modal, H100.
- App: `ap-Kinp6sRK1ecuB2dTABJERC`.
- Source: simple Track 3 base, `records/track_3_optimization/train_gpt_simple.py`.
- Setting: same as lane A.
- Seeds: trial seeds `100` and `101` via `TRACK3_SEED_BASE=0`, `TRACK3_SEED_OFFSET=100`.
- Status: detached and running. Early log confirms `track3_trial_seed=100 trial=0`, LocoProp-M owner hooks on all 12 MLP `fc` layers, and active capped corrections by step 2. Last launch-log observation reached step 41 with `step_avg=3756.26ms`.
- Log: `.opencode/modal_track3_simple_locom_target328_1xh100_laneB_2trials_20260531.launch.log`.

Read: this is the apples-to-apples follow-up to the simple Track 3 base lane where LocoProp-M materialized. It intentionally does not use the official Newton-Muon or PR291 sources. The two lanes provide four 1x-H100 seeds total while keeping each lane detached and isolated.

## Prime Simple Track 3 Base + LocoProp-M Target Runs

`track3-simple-locom-prime-a-1xh100-20260531`

- Provider: Prime Intellect, MassedCompute H100 PCIe, `$2.35/hr`.
- Pod: `8312077bfda9403fb5377b81c1e802e0`, SSH `ubuntu@216.81.248.32`.
- Source: simple Track 3 base, `records/track_3_optimization/train_gpt_simple.py`.
- Setting: 1x H100, one trial, `TRACK3_TRAIN_STEPS=3350`, `TRACK3_TARGET_LOSS=3.28`, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, all MLP `fc` surfaces, cap `0.20`.
- Seed: `200` via `TRACK3_SEED_BASE=0`, `TRACK3_SEED_OFFSET=200`.
- Status: completed and artifacts retrieved. Step 3300 validation was `3.28211`; step 3325 was `3.28096`; final step 3350 was `3.28038` at `6844.30ms/step`, missing the `3.28` target by `0.00038`. Generated script confirmed `track3_trial_seed=200 trial=0`.
- Remote logs were `/root/prime_track3_logs/track3_simple_locom_prime_a_target328_seed200.log`; local launch snapshot `.opencode/prime_track3_simple_locom_target328_seed200_1xh100_20260531.launch.log`; final artifact archive `.opencode/prime_run_snapshots_20260601/final_track3_simple_locom_seed200/seed200_final_artifacts.tgz`.

`track3-simple-locom-prime-b-1xh100-20260531`

- Provider: Prime Intellect, MassedCompute H100 PCIe, `$2.35/hr`.
- Pod: `b3ebfcf259094999b5a363fcd749e07d`, SSH `ubuntu@216.81.200.33`.
- Source: simple Track 3 base, `records/track_3_optimization/train_gpt_simple.py`.
- Setting: same as Prime lane A.
- Seed: `300` via `TRACK3_SEED_BASE=0`, `TRACK3_SEED_OFFSET=300`.
- Status: completed and artifacts retrieved. Step 3300 validation was `3.28091`; step 3325 was `3.27973`, which hit the `3.28` target; step time at the target was `6834.39ms/step`. Generated script confirmed `track3_trial_seed=300 trial=0`.
- Remote logs were `/root/prime_track3_logs/track3_simple_locom_prime_b_target328_seed300.log`; local launch snapshot `.opencode/prime_track3_simple_locom_target328_seed300_1xh100_20260531.launch.log`; final artifact archive `.opencode/prime_run_snapshots_20260601/final_track3_simple_locom_seed300/seed300_final_artifacts.tgz`.

Read: these two Prime lanes are independent one-run confirmations, separate from the two detached Modal two-trial lanes. They use the same simple Track 3 base and LocoProp-M settings, but distinct seed offsets. MassedCompute H100 throughput was about `6.84s/step`, roughly half the Modal speed observed for the same setup. The two-run outcome was near-target but not cleanly ahead: seed 200 finished at `3.28038`, while seed 300 reached `3.27973` at step 3325. Final artifacts were retrieved locally before pod cleanup.

## Modal Simple Track 3 Base + LocoProp-M 3000-Step Schedule

`track3-simple-locom-3000-h100-r1-20260601`

- Provider: Modal, H100.
- App: `ap-xrr3SwqoT5wcGGwVsWjIck`.
- Source: simple Track 3 base, `records/track_3_optimization/train_gpt_simple.py`.
- Intended setting: 1x H100, `TRACK3_TRAIN_STEPS=3000`, `TRACK3_TARGET_LOSS=3.28`, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, all MLP `fc` surfaces, cap `0.20`.
- Status: failed immediately. The Modal runner only forwards `TRACK3_*` settings through `MODAL_EXTRA_ENV_JSON`; this first launch did not do that, so it ran with default `mbs=64`, default seed, and default `sample_tokens=2048`, then OOMed after step 0.
- Local log: `.opencode/modal_track3-simple-locom-3000-h100-r1-20260601.launch.log`.

`track3-simple-locom-3000-h100-r1b-20260601`

- Provider: Modal, H100.
- App: `ap-JzZSBnBxCcchS9cE9P7qjK`.
- Source: simple Track 3 base, `records/track_3_optimization/train_gpt_simple.py`.
- Setting: 1x H100, one trial, `TRACK3_TRAIN_STEPS=3000`, `TRACK3_TARGET_LOSS=3.28`, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, all MLP `fc` surfaces, cap `0.20`.
- Seed: `400` via `TRACK3_SEED_BASE=0`, `TRACK3_SEED_OFFSET=400`.
- Status: active detached Modal run. Verified from Modal logs: `steps=3000`, `mbs=16`, `track3_trial_seed=400`, owned layers `[0..11]`, `sample_tokens=1024`; step 2 applied nonzero capped corrections and the run was at step 12 with `step_avg=4170.54ms` when local stream was disconnected.
- Local launch log: `.opencode/modal_track3-simple-locom-3000-h100-r1b-20260601.launch.log`.

Read: this is the clean long Modal lane requested after the Prime runs showed schedule-transfer ambiguity. It matches the simple Track 3 base + LocoProp-M settings used for the Prime lanes, but on a 3000-step schedule and Modal H100 throughput. The local Modal CLI was terminated after the detached remote function was verified live; `modal app list` showed `ap-JzZSBnBxCcchS9cE9P7qjK` in `ephemeral` state with one task after disconnect.

`track3-simple-locom-3100-h100-r1-20260601`

- Provider: Modal, H100.
- App: `ap-K1SLpgdRqOmgdjfTC0qvm6`; function call `fc-01KT017JZGZ40PX5DBAM8E3CKF`.
- Source: simple Track 3 base, `records/track_3_optimization/train_gpt_simple.py`.
- Setting: 1x H100, one trial, `TRACK3_TRAIN_STEPS=3100`, `TRACK3_TARGET_LOSS=3.28`, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, all MLP `fc` surfaces, cap `0.20`.
- Seed: `400` via `TRACK3_SEED_BASE=0`, `TRACK3_SEED_OFFSET=400`.
- Status: completed. Verified from Modal logs: generated `/tmp/train_gpt_simple_locoprop_m_3100.py`, `steps=3100`, `mbs=16`, `track3_trial_seed=400`, owned layers `[0..11]`, step 0 validation finite at `10.82580`; final validation reached step `3100/3100`, loss `3.29066`, with train step average near `3.60s/step` on validation and `3.67s/step` in the train loop. `modal app list` confirmed the app was `stopped` with zero tasks.
- Local launch log: `.opencode/modal_track3-simple-locom-3100-h100-r1-20260601.launch.log`.

Read: this is the direct 3100-step schedule variant requested after the 3350-step Prime lanes showed a slow late-cooldown slope. LocoProp-M is active from step 0 with the same K4/cap0.20 settings as the Prime lanes. At step `2000`, it is ahead of the completed Prime 3350-step seed-200/seed-300 mean (`3.44638`) by about `0.01335`. At step `2250`, it is ahead of the same Prime mean (`3.41077`) by about `0.01573`. At step `2625`, it is ahead of the same Prime mean (`3.36076`) by about `0.01851`. It stayed ahead through step `3000` (`3.29672` versus Prime mean `3.31280`) but missed the `3.28` target at final step `3100` by `0.01066`.

`track3-simple-locom-3250-h100-seed400-20260601`

- Provider: Modal, H100.
- App: `ap-CcmF6maCRp612wH0qElVyQ`; function call `fc-01KT0D339CHW4K2HND5D403N4A`.
- Source: simple Track 3 base, `records/track_3_optimization/train_gpt_simple.py`.
- Setting: 1x H100, one trial, `TRACK3_TRAIN_STEPS=3250`, `TRACK3_TARGET_LOSS=3.28`, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, all MLP `fc` surfaces, cap `0.20`.
- Seed: `400` via `TRACK3_SEED_BASE=0`, `TRACK3_SEED_OFFSET=400`.
- Status: active detached Modal run. Verified from Modal logs: generated `/tmp/train_gpt_simple_locoprop_m_3250.py`, `steps=3250`, `mbs=16`, `track3_trial_seed=400`, owned layers `[0..11]`, `sample_tokens=1024`.
- Local launch log: `.opencode/modal_track3-simple-locom-3250-h100-seed400-20260601.launch.log`.

Read: launched after the 3100 schedule missed target while staying materially ahead of the 3350-step Prime trajectory. The purpose is to test whether the same primitive needs roughly 3250 scheduled steps, rather than 3100, to cross `3.28`.

`track3-simple-locom-3000-h100-r2-20260601`

- Provider: Modal, H100.
- App: `ap-9EvstHYp1pkbdFTRaIQG72`; function call `fc-01KT09253D0PK918AWH7MDNHRA`.
- Source: simple Track 3 base, `records/track_3_optimization/train_gpt_simple.py`.
- Setting: 1x H100, one trial, `TRACK3_TRAIN_STEPS=3000`, `TRACK3_TARGET_LOSS=3.28`, `TRACK3_MBS=16`, `K=4`, `sample_tokens=1024`, all MLP `fc` surfaces, cap `0.20`.
- Seed: `800` via `TRACK3_SEED_BASE=0`, `TRACK3_SEED_OFFSET=800`.
- Status: active detached Modal run. Verified from Modal logs: generated `/tmp/train_gpt_simple_locoprop_m_3000.py`, `steps=3000`, `mbs=16`, `track3_trial_seed=800`, owned layers `[0..11]`, `sample_tokens=1024`. Step `125/3000` validation was `4.62976` at `3733.66ms/step`.
- Local launch log: `.opencode/modal_track3-simple-locom-3000-h100-r2-20260601.launch.log`.

Read: this is the clean 3000-step probe after the first 3000 launch OOMed and the old `r1b` lane was treated as stale/ambiguous. At the first screen, seed 800 is ahead of the completed 3350-step Prime seed-200/seed-300 mean at step 125 (`4.64782`) by about `0.01806`, so the 3000 schedule was promoted to fanout.

`track3-simple-locom-3000-h100-fanout-20260601`

- Provider: Modal, H100.
- Source/settings: same simple Track 3 base + LocoProp-M K4/cap0.20 as `r2`, with `TRACK3_TRAIN_STEPS=3000`, `TRACK3_MBS=16`, one trial per app, and `sample_tokens=1024`.
- Launcher: `tools/launch_modal_track3_locom_3000_seed.sh`.
- Seed `900`: app `ap-rAf4CKbXKOpGaG7Va96oQV`, function call `fc-01KT09M8ZXYSX6RRMEE7D3KSTZ`, launch log `.opencode/modal_track3-simple-locom-3000-h100-seed900-20260601.launch.log`, verified `track3_trial_seed=900` and entered training.
- Seed `1000`: app `ap-sSBO6YJs6gz77VULqxpC1U`, function call `fc-01KT09M90E1TN3J0XF419HX6ZX`, launch log `.opencode/modal_track3-simple-locom-3000-h100-seed1000-20260601.launch.log`, verified `track3_trial_seed=1000` and entered training.
- Seed `1100`: app `ap-JXeTJIq8c4OEUoDhqJ1EoQ`, function call `fc-01KT09M8YWRF60HFY5RY8W1M3J`, launch log `.opencode/modal_track3-simple-locom-3000-h100-seed1100-20260601.launch.log`, verified `track3_trial_seed=1100` and entered training.
- Seed `1200`: app `ap-McQsjLPw0vDWJLYEQDlWu4`, function call `fc-01KT09M8ZAAJPN5VAHPDQKYDFB`, launch log `.opencode/modal_track3-simple-locom-3000-h100-seed1200-20260601.launch.log`, verified `track3_trial_seed=1200` and entered training.
- Seed `1300`: app `ap-zOqokPl8G5j596JOnDvHy1`, function call `fc-01KT09S6GB4D836PE3EZT22RHV`, launch log `.opencode/modal_track3-simple-locom-3000-h100-seed1300-20260601.launch.log`, verified `track3_trial_seed=1300` and entered training.
- Seed `1400`: app `ap-U7JyicIiWA0qsl1qt5oPSW`, function call `fc-01KT09S6MNG93MRP4VDG258MHP`, launch log `.opencode/modal_track3-simple-locom-3000-h100-seed1400-20260601.launch.log`, verified `track3_trial_seed=1400` and entered training.
- Seed `1500`: app `ap-jQiJEaTjXEYRf7YpKr1bWp`, function call `fc-01KT09S6FMW53ZPKTDDMHXYNAJ`, launch log `.opencode/modal_track3-simple-locom-3000-h100-seed1500-20260601.launch.log`, verified `track3_trial_seed=1500` and entered training.

Read: the 3000-step Modal confirmation set reached enough early checkpoints to reject it as a full n=8 continuation and was stopped to save GPU time. The eight-seed step-125 mean was `4.64664`, only about `0.00118` ahead of the completed 3350-step Prime mean (`4.64782`). The eight-seed step-250 mean was `4.11148`, about `0.00322` worse than the Prime mean (`4.10826`). Seed 800 reached step 500 at `3.82732`, effectively parity with the Prime mean (`3.82739`). All eight 3000 apps were stopped with `modal app stop -y`; `modal app list` confirmed they were `stopped` with zero tasks. The still-active Track 3 Modal lane is the 3100-step run, which reached step `2625/3100` at `3.34224`, about `0.01851` ahead of the completed Prime 3350-step mean (`3.36076`) at the same step.

`track3-simple-locom-rmsprop-k10-start50-cap20-500-h100-r1-20260601`

- Provider: Modal, H100.
- App: `ap-0oSqlcnU4wTccGxYUrYKKD`; function call `fc-01KT01V6H7XKV5ZAF0KJBW4FP0`.
- Setting: 500-step simple Track 3, delayed start at step 50, RMSProp local optimizer, `K=10`, `TRACK3_LOCOM_INNER_LR=0.1`, explicit `TRACK3_LOCOM_NORM_CAP=0.20`.
- Status: stopped by Codex at the first active diagnostic. This was not the intended principled RMSProp run: step 50 had huge local-loss blowup (`lossK` examples `4.055e+05`, `1.611e+03`) and enormous correction norms (`~3.5e3-4.0e3`), with the cap doing all the work (`scale ~1e-4`).

`track3-simple-locom-rmsprop-k10-start50-lr1e5-cap20-500-h100-r1-20260601`

- Provider: Modal, H100.
- App: `ap-K60AbiDTWGHjq49Ig49mxA`; function call `fc-01KT024E71128JS5KG6CXMYFM1`.
- Setting: 500-step simple Track 3, delayed start at step 50, RMSProp local optimizer, `K=10`, `TRACK3_LOCOM_INNER_LR=1e-5`, explicit `TRACK3_LOCOM_NORM_CAP=0.20`, seed offset `815`.
- Status: active. Step 50 confirmed finite and locally sane: `loss0/lossK` examples `2.993e-05 -> 2.278e-05`, `2.051e-05 -> 1.828e-05`, correction norms `~0.19-0.26`, `opt=rmsprop`. Cap is present but not binding at step 50 because corrections are below `0.20 * base_step`.

Read: this is the actual capped version of the principled RMSProp/LocoProp-M lane. The cap is a safety rail for later cooldown, not an early-step scale driver at `inner_lr=1e-5`.

## 2026-06-01 LocoProp-M Diagnostic Read

The exact thing that worked in the 500-step simple-base screen was not a clean local solve. It was the capped additive correction.

Evidence from the two 500-step simple-base runs:

| Run | Step 125 | Step 250 | Step 500 | LocoProp stats |
| --- | ---: | ---: | ---: | --- |
| `modal_track3_locom_m_all_k4_mbs16_500_h100_20260531` | 4.63912 | 4.07139 | 3.74983 | prepare loss ratios mostly huge; apply/base exactly 0.20 at logged steps |
| `modal_track3_locom_m_all_k4_mbs16_500_confirm_r2_h100_20260531` | 4.64379 | 4.07186 | 3.74855 | same cap-saturated behavior |
| `modal_track3_locom_m_all_k4_mbs16_a0_control_500_h100_20260531` | 4.68004 | n/a | n/a | same prepare path but apply/base 0 |

Representative parsed stats:

- 500 r1 step 2: median `lossK/loss0 = 1.24e5`, mean `cos_desc = -0.091`, median `apply/base = 0.20`.
- 500 r1 step 10: median `lossK/loss0 = 1.36e10`, median `apply/base = 0.20`.
- 500 r1 step 125: median `lossK/loss0 = 2.79e5`, median `apply/base = 0.20`.
- 500 r2 step 250: median `lossK/loss0 = 245`, median `apply/base = 0.20`.

Read: the 500-step win is real relative to the alpha-zero control at step 125, but the local optimizer itself is usually diverging. The guardrail that made it usable was the `0.20 * base_step` cap. This should be treated as a bounded perturbation / early regularizer, not evidence that `K=4, inner_lr=0.1, prox=0.1` is a good LocoProp-M solve.

The long 8x simple-base run agrees with the 1x long runs, so distributed cancellation is not the main explanation.

| Step | 8x LocoProp | simple tuned base mean | delta vs base | official NM ref | delta vs NM |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 125 | 4.65208 | 4.67603 | -0.02395 | 4.66507 | -0.01299 |
| 250 | 4.10883 | 4.12913 | -0.02030 | 4.11784 | -0.00901 |
| 500 | 3.82689 | 3.83569 | -0.00880 | 3.82416 | +0.00273 |
| 1000 | 3.63810 | 3.64322 | -0.00512 | 3.62916 | +0.00894 |
| 1250 | 3.58144 | 3.58182 | -0.00038 | 3.56677 | +0.01467 |
| 2000 | 3.44620 | 3.44582 | +0.00038 | n/a | n/a |
| 3000 | 3.31322 | 3.31168 | +0.00154 | 3.30198 | +0.01124 |
| 3350 | 3.28003 | 3.27847 | +0.00156 | n/a | n/a |

Long-run parsed stats show the same early cap-saturation:

- 8x step 2: median `lossK/loss0 = 4.27e7`, median `apply/base = 0.20`.
- 8x step 10: median `lossK/loss0 = 3.39e13`, median `apply/base = 0.20`.
- 8x step 125: median `lossK/loss0 = 4.92e3`, median `apply/base = 0.20`.
- 8x step 1000: one printed layer is healthy (`lossK/loss0 < 1`), the other is still bad (`~1.31e3`); median `apply/base = 0.115` because one layer is no longer cap-limited and the other is.

Interpretation: the strong short-screen improvement is a start-from-zero capped perturbation plus an aggressive 500-step cooldown. In the 3350-step schedule it remains modestly helpful through roughly step 1000, then becomes neutral/worse during long refinement. Keeping the same capped perturbation active throughout the full schedule likely leaves a state that is slightly worse for final cooldown.

Two diagnostic follow-up Modal lanes are active:

- `track3-simple-locom-3000-start0-stable-h100-r1-20260601`: app `ap-ZXkryyc23Dw7xpQTO6MzF3`, seed 600, `inner_lr=0.005`, `prox=1.0`, `cap=0.05`, start step 0. Diagnostics are clean, but step 125 is `4.67998`, so this is too weak to reproduce the early signal.
- `track3-simple-locom-3000-start0-end900-k4cap20-h100-r1-20260601`: app `ap-Kc1exQhQl2dwJMM9TyFqYx`, function `fc-01KSZV9E25TDB3EKKCXMC2BE1E`, seed 700, original `K=4`, `inner_lr=0.1`, `prox=0.1`, `cap=0.20`, start step 0, end step 900. This is the direct test of the current hypothesis: keep the early cap-limited kick, then turn it off before long-schedule refinement.

## 2026-06-01 Modal 3250-Step Schedule Probe

`track3-simple-locom-3250-h100-seed400-20260601`

- Provider: Modal, H100.
- App: `ap-CcmF6maCRp612wH0qElVyQ`; function call `fc-01KT0D339CHW4K2HND5D403N4A`.
- Setting: same simple Track 3 base + LocoProp-M K4/cap0.20 primitive as the 3100/3000 probes, with `TRACK3_TRAIN_STEPS=3250`, `TRACK3_MBS=16`, seed offset `400`, `sample_tokens=1024`, target loss `3.28`.
- Status at last pull: active, only Track 3 Modal app with one task.

Early checkpoints:

| Step | 3250 seed400 | Prime 3350 mean | Delta vs Prime mean | Read |
| ---: | ---: | ---: | ---: | --- |
| 125 | 4.65000 | 4.64782 | +0.00218 | Worse early. |
| 250 | 4.11689 | 4.10826 | +0.00863 | Worse early. |
| 375 | 3.93286 | 3.92880 | +0.00406 | Still worse. |
| 500 | 3.82611 | 3.82739 | -0.00128 | Recovered to slight lead. |
| 625 | 3.75844 | 3.75842 | +0.00003 | Exact parity. |
| 750 | 3.71236 | 3.71164 | +0.00072 | Slightly worse; effectively parity. |
| 875 | 3.67128 | 3.67246 | -0.00118 | Small lead. |
| 1000 | 3.63810 | 3.63901 | -0.00091 | Small lead. |
| 1125 | 3.60779 | 3.61304 | -0.00525 | Lead reappears. |
| 1250 | 3.57779 | 3.58139 | -0.00360 | Still ahead. |
| 1500 | 3.52456 | 3.52689 | -0.00233 | Lead persists. |
| 1750 | 3.47981 | 3.48498 | -0.00517 | Lead widens. |
| 2000 | 3.44019 | 3.44638 | -0.00619 | Strong enough to replicate. |
| 2125 | 3.42299 | n/a | n/a | Between reference points. |
| 2250 | 3.40453 | 3.41077 | -0.00624 | Lead persists. |
| 2375 | 3.38726 | n/a | n/a | Between reference points. |
| 2500 | 3.37023 | 3.37834 | -0.00811 | Lead widens further. |
| 2625 | 3.35301 | 3.36076 | -0.00775 | Lead persists. |
| 2750 | 3.33674 | 3.34471 | -0.00797 | Best trajectory so far. |
| 2875 | 3.32073 | 3.32865 | -0.00792 | Late lead holds almost exactly. |
| 2925 | 3.31393 | n/a | n/a | Extra near-end eval; slope still smooth. |
| 2950 | 3.31106 | n/a | n/a | Extra near-end eval. |
| 2975 | 3.30791 | n/a | n/a | Extra near-end eval. |
| 3000 | 3.30525 | 3.31280 | -0.00755 | Still ahead, but not target yet. |
| 3025 | 3.30175 | n/a | n/a | Extra near-end eval. |
| 3050 | 3.29884 | n/a | n/a | Extra near-end eval. |
| 3075 | 3.29634 | n/a | n/a | Slope softening. |
| 3100 | 3.29373 | n/a | n/a | Tight but still plausible. |
| 3125 | 3.29152 | n/a | n/a | Needs `0.01152` over final 125 steps. |

Read: despite a weak first 375 steps, the 3250 schedule recovered by step 500, returned to parity by steps 625-750, regained a tiny lead by steps 875-1000, opened a few-millipoint lead by 1125-1250, still led at 1500, widened at 1750, and held roughly a `0.0075-0.008` lead from step 2500 through 3000. After 3000 the slope started softening; at 3125 it remains close but no longer comfortably on target pace. Keep it alive through final and use the added Modal lanes to measure variance.

Second replica:

- Run: `track3-simple-locom-3250-h100-seed500-20260601`.
- App: `ap-bZt9QGoCCHUKXrMwvsB5Se`; function call `fc-01KT0MFGPGKSMNGWSGSBNBDYX9`.
- Launch log: `.opencode/modal_track3-simple-locom-3250-h100-seed500-20260601.launch.log`.
- Verified: generated `/tmp/train_gpt_simple_locoprop_m_3250.py`, `steps=3250`, `track3_trial_seed=500`, `TRACK3_MBS=16`, `sample_tokens=1024`, all 12 MLP layers owned, and entered training.
- Early checkpoints: `4.66532 @125`, `4.11745 @250`, `3.93810 @375`, `3.82950 @500`, `3.75979 @625`, `3.71315 @750`, `3.67368 @875`, `3.63804 @1000`, `3.61104 @1125`. This started weak, recovered to a tiny lead at 1000, and was `0.00200` ahead of the Prime 3350 mean at 1125.

Current decision: finish seed400 to target, use seed500 as confirmation. Do not launch larger fanout until at least seed400 crosses `3.28` or misses narrowly with a clearly better step count than the completed 3350-step Prime runs.

Small Modal pipeline after seed400 held the late lead and seed500 recovered at 1000:

- `track3-simple-locom-3250-h100-seed1600-20260601`: app `ap-xKEhewuPirnhyhepFuBAqn`, function call `fc-01KT0R8A6AS3JP37DJJMAKQRVX`, launched with the same 3250 settings.
- `track3-simple-locom-3250-h100-seed1700-20260601`: app `ap-Pa4SuttnZdY9vCG8r6q20I`, function call `fc-01KT0R962VVMMX6PDRGPC2GFYD`, launched with the same 3250 settings.

Plot artifacts:

- `.opencode/plots/track3_locom_core_curves.png`: Prime seed200/300, Prime mean, Modal 3100 seed400, and active Modal 3250 seeds.
- `.opencode/plots/track3_locom_delta_vs_prime_mean.png`: same core runs as loss delta versus Prime 3350 two-seed mean.
- `.opencode/plots/track3_locom_all_seeds.png`: includes the stopped 3000-step Modal fanout seeds as faint lines.
- `.opencode/plots/track3_locom_seed_points.tsv` and `.opencode/plots/track3_locom_seed_summary.json`: parsed source data.

Plot read: 3250 seed400 held a real mid/late advantage, but the slope softened after roughly step 3000 and it finished at `3.28369`, missing target by `0.00369`. The 3100 seed400 had a much larger lead versus Prime mean at step 3100 (`-0.00947`) but not enough runway. Seed500 recovered by 1000-1250 (`3.57726 @1250`, `-0.00413` vs Prime mean). Seed1600 is the strongest early 3250 lane so far (`4.62203 @125`, `4.10347 @250`), while seed1700 is decent but not exceptional (`4.64194 @125`, `4.11186 @250`).

## 2026-06-01 Modal 3100 Seed400 Step-2800 Checkpoint Replay

Purpose: materialize a resumable checkpoint at the strong point of the 3100-step Modal seed400 trajectory. The original run did not save model/optimizer state, so this replays the exact simple Track 3 base + LocoProp-M setup to step 2800 and exits immediately after checkpoint save.

- App: `ap-F3KIzgPAIMjbomKRzGjiex`; function call `fc-01KT0VS9HS4V9K63A0ZP9F65MT`.
- Setting: `TRACK3_TRAIN_STEPS=3100`, `TRACK3_SEED_OFFSET=400`, linear LR schedule, simple Track 3 source, `TRACK3_MBS=16`, LocoProp-M SGD all layers, `K=4`, `sample_tokens=1024`, `inner_lr=0.1`, `prox=0.1`, `norm_cap=0.20`.
- Checkpoint controls: `TRACK3_CHECKPOINT_STEPS=2800`, `TRACK3_CHECKPOINT_DIR=/root/.cache/track3_checkpoints`, `TRACK3_CHECKPOINT_PREFIX=modal3100_locom`, `TRACK3_CHECKPOINT_EXIT_AFTER=1`, `TRACK3_TARGET_LOSS=0`.
- Expected remote file: `/root/.cache/track3_checkpoints/modal3100_locom_seed400_step2800.pt` in Modal volume `nanogpt-speedrun-cache`.
- Branch plumbing: `9243387` added checkpoint save; `3ac83bf` added resume loading and deterministic data-iterator advance.
- Launch log: `.opencode/modal_track3-simple-locom-3100-ckpt2800-h100-seed400-20260601055050.launch.log`.

Resume semantics: the payload saves `model.state_dict()`, both optimizer state dicts, CPU/CUDA RNG state, step, seed, validation loss, and LocoProp/schedule config. Resume uses `TRACK3_RESUME_CHECKPOINT=<path>` and advances the deterministic train loader by the saved step before entering `range(start_step, train_steps + 1)`.

Diagnosis of the late miss:

- `3100 seed400` looked strong at step 2800 (`3.31815`) but still needed `0.03815` loss in the final 300 steps. It actually dropped `0.02749`, finishing `0.01066` above target.
- The linear 3100 schedule is nearly dead late: LR multiplier is `0.138` at 2800, `0.046` at 3000, and zero at 3100. The final 100 steps only drop `0.00606`.
- Extending to 3250 adds runway but changes the absolute-step schedule. At 2875, 3250 seed400 is `3.32073` while 3100 seed400 is `3.30966`; the longer run is less cooled down and therefore loses part of the apparent 2800 advantage.
- The 3250 seed400 lead versus Prime mean shrinks from roughly `0.008` around 2875-3000 to `0.0012` at 3250. So the primitive is mostly a mid-cooldown/trajectory-shaping gain, not a terminal landing gain.
- Late LocoProp diagnostics show weak descent alignment: printed `cos_desc` values are usually small (`~0.03-0.05`) and sometimes near-zero or negative. Since `TRACK3_LOCOM_NORM_CAP=0.20` is tied to the base Muon step norm, the LocoProp displacement also collapses with LR exactly when the run needs terminal force.

Suffix experiment ladder once the 2800 checkpoint lands:

1. Resume original 3100 tail to verify checkpoint fidelity.
2. Resume with LocoProp disabled after 2800 to test whether late LocoProp hurts polish.
3. Resume to 3150/3200/3250 from the strong 2800 state to isolate runway from early trajectory.
4. Resume with a LocoProp cap floor or normalized correction so local displacement does not vanish with the base LR.
5. Test the PR287-style landing schedule from the same checkpoint before spending another full replay.

## 2026-06-01 3000-Step PR287 Schedule Probe

Rationale: existing 3000-step lanes are not yet strong enough to fan out to n=8. The `cooldown_frac=0.5` lane is behind by step 1125, and the naive `power05` lane is only mildly positive at step 1000. To test a stronger landing without changing the LocoProp-M primitive or adding Soft-Muon, the generator now supports `TRACK3_LR_SCHEDULE=pr287`.

- Commit: `9bad265` (`Add Track 3 PR287 schedule mode`).
- App: `ap-2Y3C3pJk7djppdrNgen7YH`; function call `fc-01KT0YF4X0HGN7X9DEJAMS9Y7P`.
- Launch log: `.opencode/modal_track3-simple-locom-3000-pr287-h100-seed2200-20260601063754.launch.log`.
- Setting: `TRACK3_TRAIN_STEPS=3000`, `TRACK3_SEED_OFFSET=2200`, `TRACK3_LR_SCHEDULE=pr287`, `TRACK3_LR_POWER=1.2`, `TRACK3_LR_SCHEDULE_STEPS=3065`, target `3.28`, simple Track 3 base + LocoProp-M K4/cap0.20.
- Status at launch verification: alive, generated `/tmp/train_gpt_simple_locoprop_m_3000.py`, seed `2200`, all 12 MLP layers owned, no traceback.

Decision gate: do not fan this out until it is clearly ahead by the 1000-1500 window. A weak sub-`0.003` lead at 1000 is not enough; the previous `power05` lane already showed that level without being promotion-ready.

Stop decision: user asked to keep this last probe down and finish the already-running lanes first. Stopped with `modal app stop -y ap-2Y3C3pJk7djppdrNgen7YH` after the first validation point.

- Last validation: `4.63808 @125`, with step-average around `3745ms`.
- Final log tail: app stopped from CLI at step `152`; runner terminated after step `153`.
- Read: first point was better than the other live 3000-step lanes at `125`, but it was too early to justify keeping an extra GPU lane alive under the current run-budget priority.

## 2026-06-01 Active Modal Lane Snapshot After PR287 Stop

Remaining live lanes are the checkpoint replay plus existing 3250/3000 probes:

- `ap-F3KIzgPAIMjbomKRzGjiex`: 3100 seed400 checkpoint replay, latest `3.67397 @875`; purpose is to save the step-2800 checkpoint, not score this as a new independent result.
- `ap-bZt9QGoCCHUKXrMwvsB5Se`: 3250 seed500, latest `3.32254 @2875` at this pull; healthy and modestly positive versus the Prime 3350 mean, but not ahead of the original 3100 seed400 hot curve.
- `ap-xKEhewuPirnhyhepFuBAqn`: 3250 seed1600, latest `3.48054 @1750`; healthy and similar to the prior good 3250 lane.
- `ap-Pa4SuttnZdY9vCG8r6q20I`: 3250 seed1700, latest `3.48163 @1750`; healthy, nearly tied with seed1600.
- `ap-eIPcDkgAqaJf8OjnBkZ7DW`: 3000 cooldown-frac-0.5 seed1800, latest `3.57887 @1375`; not hot versus the 3350 reference trajectory.
- `ap-sgmLmoef9czMVD4rzk82xK`: 3000 naive power05 seed1900, latest `3.58265 @1250`; mild/neutral, not promotion-ready.

Clarification: "ahead" for seed500 means ahead of the Prime 3350 mean only. At matched steps, original 3100 seed400 remains materially better: `3.30966 @2875` versus seed500 `3.32254 @2875` (`+0.01288` worse), and `3.30127 @2950` versus seed500 `3.31284 @2950` (`+0.01157` worse). Seed500 is therefore useful as a 3250 replication/variance lane, not evidence that the 3100 hot trajectory replicated.

Update after the next poll:

- Seed500 reached `3.30725 @3000`, still much worse than original 3100 seed400 `3.29672 @3000` (`+0.01053`) and only modestly ahead of the Prime 3350 mean `3.31280 @3000` (`-0.00555`).
- User asked to stop the two extra 3250 replica lanes because they looked likely to follow the same weak replication pattern.
- Stopped `ap-xKEhewuPirnhyhepFuBAqn` (seed1600) with `modal app stop -y`; last completed validation was `3.45936 @1875`, final tail terminated around step `1980`.
- Stopped `ap-Pa4SuttnZdY9vCG8r6q20I` (seed1700) with `modal app stop -y`; last completed validation was `3.46110 @1875`, final tail terminated around step `1964`.
- Read: the later 3250 replicas were not reproducing the large original 3100 hot curve, so they are not worth paying to finish under the current n=8-below-3000 objective.

## 2026-06-01 Remaining Lane Refresh

Active Modal Track 3 apps after stopping PR287/seed1600/seed1700:

- `ap-bZt9QGoCCHUKXrMwvsB5Se`: 3250 seed500 still active, latest `3.30366 @3025`. This is ahead of the Prime 3350 mean but still behind original 3100 seed400 by about `0.00921` at matched step `3025` (`3.29445` vs `3.30366`).
- `ap-eIPcDkgAqaJf8OjnBkZ7DW`: 3000 cooldown-frac-0.5 seed1800 still active, latest `3.55969 @1500`; behind the Prime mean `3.52689 @1500`, so not a fanout candidate.
- `ap-sgmLmoef9czMVD4rzk82xK`: 3000 naive power05 seed1900 still active, latest `3.56142 @1375`; roughly `+0.00697` worse than Prime mean at `1375`, so not a fanout candidate.
- `ap-F3KIzgPAIMjbomKRzGjiex`: 3100 seed400 checkpoint replay still active, latest `3.63443 @1000`; no checkpoint artifact yet.

Modal volume check: root of `nanogpt-speedrun-cache` does not yet show `track3_checkpoints`, which is expected because the replay has not reached step `2800`.

Action: hold launches. No current 3000 lane has the strength needed to justify n=8 fanout. Let seed500 finish for a clean endpoint and keep waiting for the step-2800 checkpoint replay.

## 2026-06-01 Follow-Up Refresh

Active owned Modal apps remain `ap-bZt9QGoCCHUKXrMwvsB5Se`, `ap-eIPcDkgAqaJf8OjnBkZ7DW`, `ap-sgmLmoef9czMVD4rzk82xK`, and `ap-F3KIzgPAIMjbomKRzGjiex`. Unrelated active app `ap-pKCCaFOpuFBJ3mWcPMVW4G` is a `dw-pr` lane and was not touched.

- `ap-bZt9QGoCCHUKXrMwvsB5Se`: 3250 seed500 reached `3.29109 @3150`. This still mirrors the 3250 late-miss profile: useful endpoint data, but not a 3000-step confirmation path.
- `ap-eIPcDkgAqaJf8OjnBkZ7DW`: 3000 cooldown-frac-0.5 seed1800 reached `3.53635 @1625`; still weak versus the reference trajectory.
- `ap-sgmLmoef9czMVD4rzk82xK`: 3000 naive power05 seed1900 reached `3.53560 @1500`; also weak versus the reference trajectory and not fanout-worthy.
- `ap-F3KIzgPAIMjbomKRzGjiex`: 3100 seed400 checkpoint replay reached `3.60429 @1125`; still healthy, but not near the step-2800 checkpoint save yet.

Modal volume check still shows no `track3_checkpoints` entry under `nanogpt-speedrun-cache`, expected at this point.

Decision: no new launches. The only action with value is to let seed500 finish and keep the replay alive until the step-2800 checkpoint lands. The active 3000 lanes do not support an n=8 below-3000 fanout.

## 2026-06-01 Endpoint And Stop Refresh

Stopped the two remaining 3000-step simple-base + LocoProp-M schedule probes because both were clearly below the fanout gate:

- `ap-eIPcDkgAqaJf8OjnBkZ7DW`: 3000 cooldown-frac-0.5 seed1800. Last validation before stop was `3.53635 @1625`; final tail stopped around step `1750`.
- `ap-sgmLmoef9czMVD4rzk82xK`: 3000 naive power05 seed1900. Last validation before stop was `3.52127 @1625`; final tail stopped around step `1649`.

Let `ap-bZt9QGoCCHUKXrMwvsB5Se` finish:

- 3250 seed500 final: `3.28566 @3250`, missing target by `0.00566`.
- Comparison: original 3250 seed400 final was `3.28369 @3250`, so seed500 is worse by `+0.00197`. Both miss target and neither supports a 3000-step PR confirmation.
- App state after finish: stopped.

Replay/checkpoint status:

- `ap-F3KIzgPAIMjbomKRzGjiex`: still active, latest `3.57335 @1250`.
- Modal volume `nanogpt-speedrun-cache` still has no `track3_checkpoints` entry, expected because replay is not near step `2800`.

Current Modal Track 3 ownership state: only the 3100 seed400 checkpoint replay remains active. The active `dw-pr` app is unrelated and was not touched.

Decision: no n=8 fanout. The 3000 schedule attempts were weak and both 3250 replicas missed target. Continue only to preserve the step-2800 replay checkpoint for suffix experiments.

## 2026-06-01 Relaunched 3000 PR287 Probe

After the weak active lanes were stopped and seed500 finished, the only simple-base + LocoProp-M 3000 schedule that had not received a meaningful run was the PR287-style schedule. The previous PR287 probe was stopped at step `153` by request, after only `4.63808 @125`.

Launched exactly one new PR287 probe, gated to 1000-1500 before any fanout:

- App: `ap-WFwx1F0kuxLQqKc80wDXt3`.
- Function call: `fc-01KT10RDMVHB0RHGXZF71C7FSR`.
- Run: `track3-simple-locom-3000-pr287-h100-seed2300-20260601071741`.
- Launch log: `.opencode/modal_track3-simple-locom-3000-pr287-h100-seed2300-20260601071741.launch.log`.
- Setting: `TRACK3_TRAIN_STEPS=3000`, `TRACK3_SEED_OFFSET=2300`, `TRACK3_LR_SCHEDULE=pr287`, `TRACK3_LR_POWER=1.2`, `TRACK3_LR_SCHEDULE_STEPS=3065`, simple Track 3 base + LocoProp-M K4/cap0.20, H100, nproc=1, target `3.28`.
- Launch verification: app is active/detached, generated `/tmp/train_gpt_simple_locoprop_m_3000.py`, `track3_trial_seed=2300`, all 12 LocoProp layers owned.

Decision gate: if this does not show a clear lead by `1000-1500`, stop it. Do not launch n=8 until a 3000 schedule is clearly hot.

First validation:

- PR287 seed2300: `4.64980 @125`, step average `3688.86ms`.
- Read: not encouraging. It is worse than Prime 3350 mean `4.64781 @125` and worse than the stopped PR287 seed2200 first point `4.63808 @125`.
- Action: keep running only to the next screens because the real gate is `1000-1500`; no fanout.

Checkpoint replay side status at the same refresh:

- `ap-F3KIzgPAIMjbomKRzGjiex`: replay reached `3.51878 @1500`; still healthy, not yet near step-2800 checkpoint.
- Modal volume still has no `track3_checkpoints` entry.

User redirected to stop PR287 and keep the 3100 replay as the primary run:

- PR287 app `ap-WFwx1F0kuxLQqKc80wDXt3` was stopped; Modal reported it had already been stopped by the time the stop command ran.
- Final PR287 tail: stopped around step `231`, with only the first validation available (`4.64980 @125`).
- App state after confirmation: stopped.
- Current Track 3 owned active state: only `ap-F3KIzgPAIMjbomKRzGjiex` remains active.

Batch-size clarification:

- Source Track 3 training uses `batch_size = 8 * 64 * 1024 = 524288` tokens per optimizer step.
- With `seq_len=1024`, that is `512` sequences per optimizer step globally.
- In these 1x H100 Modal runs, the launcher sets `TRACK3_MBS=16`, so the fixed global batch is accumulated as `32` microbatches of `16` sequences each.
- LocoProp-M statistics use `TRACK3_LOCOM_SAMPLE_TOKENS=1024`; this is the local correction sample size, not the training batch size.

Replay tracking refresh:

- `ap-F3KIzgPAIMjbomKRzGjiex` reached `3.47622 @1750`.
- Original 3100 seed400 was `3.47400 @1750`, so replay is `+0.00222` worse at this checkpoint.
- Read: still tracking close enough to trust for the step-2800 checkpoint replay purpose.
- Action: keep the replay running to step `2800`; no other Track 3 owned app is active.

Replay tracking refresh 2:

- `ap-F3KIzgPAIMjbomKRzGjiex` reached `3.45489 @1875` and `3.43471 @2000`.
- Original 3100 seed400 was `3.45382 @1875` and `3.43303 @2000`, so replay is `+0.00107` and `+0.00168` worse at those matched checkpoints.
- Current train speed remains stable around `3627ms/step`; from step `2000`, the step-2800 checkpoint is roughly 48-50 minutes away.
- Modal volume `nanogpt-speedrun-cache` still has no `track3_checkpoints` entry, expected because the replay has not reached step `2800`.
- Decision: no n=8 fanout and no new 3000 launch. All 3000 schedule probes so far failed the gate, and this replay is only to materialize the strong step-2800 state for suffix experiments.

Replay tracking refresh 3 and suffix-array prep:

- Updated goal: once the step-2800 checkpoint lands, launch an array of suffix runs from that state to find a path to `3.28` at `<=3100`, preferably `<=3030`.
- Replay reached `3.41608 @2125` and `3.39727 @2250`.
- Original 3100 seed400 was `3.41412 @2125` and `3.39504 @2250`, so replay is `+0.00196` and `+0.00223` worse at those matched checkpoints.
- Step-2250 LocoProp diagnostics: l0-l2 corrections are small, mildly aligned, and mostly uncapped; l3 has negative `cos_desc` and is heavily capped. This motivates suffix lanes that vary late LocoProp cap, plus a no-late-LocoProp control.
- Added `tools/launch_modal_track3_locom_resume_suffix_array.sh` to launch the checkpoint suffix grid immediately after the Modal-volume checkpoint appears.
- Also widened `tools/launch_modal_track3_locom_3000_seed.sh` env passthrough so suffix lanes can vary LocoProp cap/alpha/steps/logging and source/mbs/seed settings without hand-building JSON.
- Planned suffix lanes from `modal3100_locom_seed400_step2800.pt`: exact 3100 fidelity, 3030 power tails (`power=0.50/0.35`, cap `0.20/0.50`), 3030 PR287-style tails (`schedule_steps=3065`, cap `0.20/0.50`), 3100 power fallbacks, and 3100 no-late-LocoProp control.

## 2026-06-01 Step-2800 Suffix Results and LR-Floor Probe

The replay checkpoint landed and was saved in Modal volume `nanogpt-speedrun-cache`:

- Checkpoint: `/root/.cache/track3_checkpoints/modal3100_locom_seed400_step2800.pt`.
- Replay value: `3.32043 @2800`; original 3100 seed400 value was `3.31815 @2800`, so the replay checkpoint is about `+0.00228` worse but close enough for suffix-search purposes.
- Resume lanes load this checkpoint with optimizer state plus CPU/CUDA RNG state and advance the deterministic data loader by the saved step.

Initial suffix-array outcomes:

- Exact 3100 fidelity (`ap-QcBdtzR3EUpRzXV7GqbHnh`): final `3.29279 @3100`, miss by `0.01279`.
- 3100 no-late-LocoProp (`ap-0wXGZcfvVOjT6HM7SNZZZo`): final `3.29267 @3100`, miss by `0.01267`; slightly better than fidelity but not enough.
- 3030 linear cap0.20 (`ap-mlYvGiAAXPeRD0HomuoSTy`): final `3.29696 @3030`, miss by `0.01696`.
- 3030 linear cap0.50 (`ap-2yxnsm1GC3AGkvEVbAupsz`): final `3.29714 @3030`, miss by `0.01714`.
- 3030 PR287 schedule_steps=3065 cap0.20 (`ap-ESCBCX09CLtifBrkufpDT5`): stopped after `3.29725 @3025`; could not plausibly reach target by `3030`.
- 3030 PR287 schedule_steps=3065 cap0.50 (`ap-cCqNWnVkhHjj4PQLo5PAAG`): stopped after `3.29737 @3025`; could not plausibly reach target by `3030`.
- Power-tail lanes (`power=0.50/0.35`) spiked early validation and were stopped; they were too hot from the checkpoint.

Read: the suffix is consistently flattening well above target. This is not a working <=3030 or <=3100 PR-confirmation path, and it does not justify n=8 fanout.

To test whether the taper is simply too-cold LR, added `TRACK3_LR_MIN_ETA` to the generator/launcher and pushed commit `1d0eba8` (`Add Track 3 suffix LR floor`). This floors only the linear/power cooldown multiplier and leaves PR287 unchanged. Smoke check: generated 3030 script compiled and prints/logs `lr_min_eta`.

LR-floor probe launches:

- `ap-U80DH4VfTAfsH8a3JcB6f4`: `s3030-linear-floor008-cap020`, stopped after `3.30477 @2925`; worse than plain linear cap0.20 at the same step (`3.30337 @2925`).
- `ap-KtxcN0v55IqDAxkvYD4q1c`: `s3030-linear-floor012-cap020`, stopped after `3.31271 @2875`; floor `0.12` was clearly too hot.
- `ap-qjxBh8oWe5sv5ciC8Is66I`: `s3030-pr2873100-cap020`, stopped after `3.30866 @2875`; later PR287 endpoint was behind the earlier `schedule_steps=3065` PR287 lane (`3.30783 @2875`).
- `ap-IO90Av4ImKhO8l6Azni83w`: `s3030-linear-floor008-nolate`, stopped after `3.30675 @2900`; not on pace.
- `ap-EqVhA57Tnyy6CYcOZDB40j`: `s3100-linear-floor008-nolate`, stopped after `3.30368 @2950`; this was worse than old 3100 no-late at the same step (`3.30337 @2950`).

Interpretation: "higher LR for some time" did not rescue the checkpoint. Aggressive floor/power variants degrade quickly. Mild floor with active LocoProp also underperformed. Mild floor with late LocoProp disabled was no better than the old no-late 3100 control by the first post-floor checkpoints. This argues the taper is not merely too-cold LR; the step-2800 checkpoint appears to be on a trajectory that flattens above target under these suffix knobs.

## 2026-06-01 Step-2400 LocoProp Checkpoint Replay

User requested saving the step-2400 LocoProp state as well, analogous to the saved step-2800 replay checkpoint.

The already-running `3030-end2400` probe was not launched with checkpoint env, so it could not save a state. It was stopped early:

- App: `ap-DavdVDWbiYpfjF00YNd4Mv`.
- Run: `track3-simple-locom-3030-end2400-h100-seed2400-20260601094620`.
- Last validation before stop: `4.64419 @125`.
- Preserved log: `.opencode/suffix_final_logs_20260601/track3-simple-locom-3030-end2400-seed2400-preckpt_ap-DavdVDWbiYpfjF00YNd4Mv.log`.

Relaunched same seed/settings with checkpoint save at step 2400 and exit:

- App: `ap-dlp4N4VBafETgu7QOcHVWM`.
- Function call: `fc-01KT19TEF2TWBZPWVZHGZAVSY0`.
- Run: `track3-simple-locom-3030-end2400-ckpt2400-h100-seed2400-20260601095630`.
- Setting: `TRACK3_TRAIN_STEPS=3030`, `TRACK3_SEED_OFFSET=2400`, simple Track 3 source, `TRACK3_MBS=16`, LocoProp-M SGD all layers, `K=4`, `sample_tokens=1024`, `inner_lr=0.1`, `prox=0.1`, `norm_cap=0.20`, `TRACK3_LOCOM_END_STEP=2400`.
- Checkpoint controls: `TRACK3_CHECKPOINT_STEPS=2400`, `TRACK3_CHECKPOINT_DIR=/root/.cache/track3_checkpoints`, `TRACK3_CHECKPOINT_PREFIX=modal3030_locom_end2400`, `TRACK3_CHECKPOINT_EXIT_AFTER=1`, `TRACK3_TARGET_LOSS=0`.
- Expected checkpoint: `/root/.cache/track3_checkpoints/modal3030_locom_end2400_seed2400_step2400.pt` in Modal volume `nanogpt-speedrun-cache`.
- Validation cadence: `SCREEN_VAL_EVERY=120` so step `2400` is definitely a validation/checkpoint step. Default 125-step validation would skip 2400 in a 3030-step run.
- Launch verification: app active/detached on H100; generated `/tmp/train_gpt_simple_locoprop_m_3030.py`, `track3_trial_seed=2400`, all 12 LocoProp layers owned, initial validation `10.82580 @0`.

Superseded next action: this run was aborted after the seed/trajectory mismatch was noticed. Do not poll or use `modal3030_locom_end2400_seed2400_step2400.pt`.

Correction: the `ap-dlp4N4VBafETgu7QOcHVWM` step-2400 replay above was the wrong trajectory for the user's requested paired state. It used seed offset `2400` and a `3030`/`end2400` schedule, not the same `3100`/seed400 LocoProp trajectory as the saved step-2800 checkpoint. It was aborted after initial validation and should not be used as the matching step-2400 image.

Corrected step-2400 checkpoint replay launch:

- App: `ap-JFKJK9m9uwGDSU85IiidwP`.
- Function call: `fc-01KT1A54DG0385HT1TDF3VSGPD`.
- Run: `track3-simple-locom-3100-ckpt2400-h100-seed400-20260601100220`.
- Setting: `TRACK3_TRAIN_STEPS=3100`, `TRACK3_SEED_OFFSET=400`, simple Track 3 source, `TRACK3_MBS=16`, LocoProp-M SGD all layers, `K=4`, `sample_tokens=1024`, `inner_lr=0.1`, `prox=0.1`, `norm_cap=0.20`, no `TRACK3_LOCOM_END_STEP`.
- Checkpoint controls: `TRACK3_CHECKPOINT_STEPS=2400`, `TRACK3_CHECKPOINT_DIR=/root/.cache/track3_checkpoints`, `TRACK3_CHECKPOINT_PREFIX=modal3100_locom`, `TRACK3_CHECKPOINT_EXIT_AFTER=1`, `TRACK3_TARGET_LOSS=0`.
- Validation cadence: `SCREEN_VAL_EVERY=120`, because the checkpoint hook runs inside validation and `2400` is not on the default 125-step cadence.
- Launch verification: app active/detached on H100; generated `/tmp/train_gpt_simple_locoprop_m_3100.py`, `track3_trial_seed=400`, all 12 LocoProp layers owned.
- Expected checkpoint: `/root/.cache/track3_checkpoints/modal3100_locom_seed400_step2400.pt` in Modal volume `nanogpt-speedrun-cache`.
- Local launch log: `.opencode/modal_track3-simple-locom-3100-ckpt2400-h100-seed400-20260601100220.launch.log`.

Status refresh:

- App still active: `ap-JFKJK9m9uwGDSU85IiidwP`.
- Latest validation observed: `3.50705 @1560`.
- Step average: about `3679.7ms/step`; validation step average around `3675.7ms/step`.
- No `track3_checkpoint_saved` line yet; target checkpoint remains step `2400`.
- Approximate ETA from step `1560` to checkpoint: 51-52 minutes at current cadence.
- No `Traceback`, `Error`, `Exception`, or runner termination observed in the inspected log tail.

Status refresh 2:

- App still active: `ap-JFKJK9m9uwGDSU85IiidwP`.
- Latest validation observed: `3.44637 @1920`.
- Step average: about `3679.3ms/step`.
- No `track3_checkpoint_saved` line yet; target checkpoint remains step `2400`.
- Approximate ETA from step `1920` to checkpoint: about 30 minutes at current cadence.
- No `Traceback`, `Error`, `Exception`, or runner termination observed in the inspected log tail.

## 2026-06-01 LocoProp Norm-Cap Window Probe

Added an env-driven cap-window knob for LocoProp-M:

- Code commit: `785dcf3` (`Add Track 3 LocoProp norm cap windows`).
- Env: `TRACK3_LOCOM_NORM_CAP_WINDOWS=start:end:value`, comma-separated for multiple windows.
- Default behavior unchanged: if the env var is empty, the static `TRACK3_LOCOM_NORM_CAP` is used.
- Apply diagnostics now log the effective `cap=...` beside `base_step`, `corr_norm`, and `scale`.

Launched a separate H100 Modal run requested by the user, with the LocoProp norm cap rising from `0.20` to `0.40` for steps `1600-2400`:

- App: `ap-DRieR7b1nuvh9QeZzA91P3`.
- Function call: `fc-01KT1HGP66ER5C3GDBQRZW9ZA3`.
- Run: `track3-simple-locom-3100-capwin040-1600-2400-h100-seed400-20260601121047`.
- Setting: `TRACK3_TRAIN_STEPS=3100`, `TRACK3_SEED_OFFSET=400`, simple Track 3 source, `TRACK3_MBS=16`, LocoProp-M SGD all layers, `K=4`, `sample_tokens=1024`, `inner_lr=0.1`, `prox=0.1`, base `norm_cap=0.20`, `TRACK3_LOCOM_NORM_CAP_WINDOWS=1600:2400:0.40`.
- Local launch log: `.opencode/modal_track3-simple-locom-3100-capwin040-1600-2400-h100-seed400-20260601121047.launch.log`.
- Launch verification: app active/detached on H100; generated `/tmp/train_gpt_simple_locoprop_m_3100.py`, `track3_trial_seed=400`, all 12 LocoProp layers owned.
- Early diagnostic verification: `locoprop_m_apply` at steps `0`, `1`, and `2` shows effective `cap=0.200`, as expected before the `1600-2400` window.
- Next check: at step `1600`, verify `locoprop_m_apply step=1600` logs `cap=0.400`; compare validation against the original seed400 3100 trajectory and the checkpoint replay.

## 2026-06-01 Step-2400 Checkpoint and Pre-3000 Suffix Array

The corrected step-2400 checkpoint replay completed exactly as intended:

- App: `ap-JFKJK9m9uwGDSU85IiidwP`.
- Final checkpoint validation: `3.37491 @2400`.
- Save log: `track3_checkpoint_saved step:2400 path:/root/.cache/track3_checkpoints/modal3100_locom_seed400_step2400.pt val_loss:3.3749122619628906`.
- Modal-volume verification: `modal volume ls nanogpt-speedrun-cache /track3_checkpoints` shows `track3_checkpoints/modal3100_locom_seed400_step2400.pt` and the earlier `modal3100_locom_seed400_step2800.pt`.

Because the checkpoint replay used `TRACK3_CHECKPOINT_EXIT_AFTER=1`, it stopped after save. A direct same-settings continuation was launched from the saved checkpoint:

- App: `ap-dFrT1wOrSJtpVNdU6fhvtS`.
- Function call: `fc-01KT1K98KR4AZYFM416VWJJFM4`.
- Run: `track3-simple-locom-3100-resume2400-toend-h100-seed400-20260601124152`.
- Setting: same seed400/simple-Track3/LocoProp-M K4/cap0.20 path, `TRACK3_RESUME_CHECKPOINT=/root/.cache/track3_checkpoints/modal3100_locom_seed400_step2400.pt`, `TRACK3_RESUME_ADVANCE_DATA=1`, `TRACK3_RESUME_RESTORE_RNG=1`, `TRACK3_TRAIN_STEPS=3100`, `TRACK3_TARGET_LOSS=0`.
- Launch verification: remote log printed `track3_checkpoint_loaded path:/root/.cache/track3_checkpoints/modal3100_locom_seed400_step2400.pt step:2400 seed:400 val_loss:3.3749122619628906`.
- Local launch log: `.opencode/modal_track3-simple-locom-3100-resume2400-toend-h100-seed400-20260601124152.launch.log`.

User then requested multiple suffixes that must reach target before 3000. Added `tools/launch_modal_track3_locom_resume2400_pre3000_array.sh` and launched the pre-3000 array from the step-2400 checkpoint:

- Code commit: `21e2f1a` (`Add Track 3 pre-3000 resume suffix grid`).
- Wrapper launch log: `.opencode/modal_track3-s2400-pre3000-array-20260601124348.launch.log`.
- Common resume settings: `TRACK3_RESUME_CHECKPOINT=/root/.cache/track3_checkpoints/modal3100_locom_seed400_step2400.pt`, `TRACK3_SEED_OFFSET=400`, `TRACK3_RESUME_ADVANCE_DATA=1`, `TRACK3_RESUME_RESTORE_RNG=1`, `TRACK3_TARGET_LOSS=3.28`, `SCREEN_VAL_EVERY=25`, H100.
- All lanes have `TRACK3_TRAIN_STEPS=3000`, so any target crossing is at or before step 3000.

Pre-3000 lane roster:

- `ap-BoBw1WtxypXNBUxBdY7XsO`: `fid3000-linear-cap020`, exact linear/cap0.20 continuation to 3000. First suffix validation: `3.36810 @2425`.
- `ap-4au2IK8zcJNStwy4edfPwt`: `s3000-linear-nolate`, no LocoProp after the saved step via `TRACK3_LOCOM_END_STEP=2400`. This is the explicit no-LocoProp-post-2400 control the user asked about. It loaded `modal3100_locom_seed400_step2400.pt`; a log search for `locoprop_m_apply` returned no entries, consistent with LocoProp being disabled after resume. Latest sampled values: `3.36770 @2425`, `3.36190 @2450`, `3.35877 @2475`, `3.35466 @2500`, `3.35145 @2525`, `3.34702 @2550`, `3.34287 @2575`, `3.33950 @2600`.
- `ap-nyNB5ezTrYdpeRPdIYdi0u`: `s3000-power050-cap020`, power-0.50 LR tail, cap0.20. First suffix validation: `3.39932 @2425`, already worse than fidelity at the same point.
- `ap-p2YpByjsy6QM2A4yR5CgGu`: `s3000-power050-cap040`, power-0.50 LR tail, cap0.40. Active, pending first parsed validation at last check.
- `ap-dm9efGOnbYSrs3Zr12H7qR`: `s3000-power035-cap040`, power-0.35 LR tail, cap0.40. Loaded checkpoint and printed `3.37491 @2400`.
- `ap-71kmMnKYH9SkULGzSRIjBq`: `s3000-pr2873065-cap020`, PR287-style LR with schedule steps 3065, cap0.20. Loaded checkpoint and printed `3.37491 @2400`.
- `ap-Ud1Jbwluq0wrdNV2HStcVW`: `s3000-pr2873065-cap040`, PR287-style LR with schedule steps 3065, cap0.40. Verified active correction at step 2400 with `cap=0.400`.
- `ap-EY4AwEODxLRRStI4t4IN60`: `s3000-linear-capwin040-2400-3000`, linear LR with base cap0.20 and `TRACK3_LOCOM_NORM_CAP_WINDOWS=2400:3000:0.40`. Verified active correction at step 2400 with `cap=0.400`.

Current read: the 2400 checkpoint is earlier and higher-loss than the 2800 checkpoint, so the suffixes need to make up about `0.095` loss by step 3000. The fidelity lane's first step-2425 value (`3.36810`) is the early reference. The power-0.50 cap0.20 lane is immediately worse (`3.39932 @2425`) and should be killed early unless it sharply recovers.

The bad power-plus-LocoProp lanes were stopped to save GPU:

- `ap-nyNB5ezTrYdpeRPdIYdi0u`: `s3000-power050-cap020`, stopped after `3.39932 @2425`, `3.40366 @2450`, `3.40593 @2475`, `3.40505 @2500`.
- `ap-p2YpByjsy6QM2A4yR5CgGu`: `s3000-power050-cap040`, stopped before useful trajectory.
- `ap-dm9efGOnbYSrs3Zr12H7qR`: `s3000-power035-cap040`, stopped after `3.41995 @2425`, `3.44000 @2450`, `3.43877 @2475`, `3.44630 @2500`.

Because no-LocoProp-after-2400 was close to the active-LocoProp lanes and avoids the late correction risk, launched three additional no-late rescue suffixes from the same step-2400 checkpoint:

- `ap-dqkxpnQ5w54UhjBDWmwbvF`: `s3000-pr2873065-nolate`, PR287-style LR with schedule steps 3065, `TRACK3_LOCOM_END_STEP=2400`. Launch log: `.opencode/modal_track3-s2400-pre3000-s3000-pr2873065-nolate-seed400-20260601131033.launch.log`. First parsed value: `3.36631 @2425`.
- `ap-Jx1dqCUlm8IzVHjKi8jzZn`: `s3000-power050-nolate`, power-0.50 LR tail, `TRACK3_LOCOM_END_STEP=2400`. Launch log: `.opencode/modal_track3-s2400-pre3000-s3000-power050-nolate-seed400-20260601131033.launch.log`. It loaded the 2400 checkpoint and is waiting for the first post-resume validation.
- `ap-TmrkYyIYXZuYswF7A888Dj`: `s3000-linear-floor004-nolate`, linear LR with `TRACK3_LR_MIN_ETA=0.04`, `TRACK3_LOCOM_END_STEP=2400`. Launch log: `.opencode/modal_track3-s2400-pre3000-s3000-linear-floor004-nolate-seed400-20260601131033.launch.log`. App showed zero tasks and no logs at the first post-launch check, so relaunch if it remains empty.

2026-06-01 later status pass:

- `ap-Jx1dqCUlm8IzVHjKi8jzZn` was stopped after worsening to `3.40517 @2475` from the `3.37491 @2400` checkpoint.
- `ap-TmrkYyIYXZuYswF7A888Dj` was stopped because it stayed at zero tasks/no logs.
- Relaunched the linear floor no-late rescue as `ap-2rie7tf5m8Dd90XGk6h90U` with the same step-2400 checkpoint, `TRACK3_LOCOM_END_STEP=2400`, and `TRACK3_LR_MIN_ETA=0.04`. Launch log: `.opencode/modal_track3-s2400-pre3000-s3000-linear-floor004-nolate-retry-seed400-20260601132050.launch.log`.
- Latest leading status at this pass:
  - `ap-dFrT1wOrSJtpVNdU6fhvtS` (`3100 resume2400 exact cap0.20`): `3.30043 @2975`; not on pace for a pre-3000 hit.
  - `ap-BoBw1WtxypXNBUxBdY7XsO` (`3000 fid linear cap0.20`): `3.30578 @2875`; leading 3000-deadline lane, but still needs a large late bend.
  - `ap-71kmMnKYH9SkULGzSRIjBq` (`3000 PR287 cap0.20`): `3.30726 @2850`.
  - `ap-Ud1Jbwluq0wrdNV2HStcVW` (`3000 PR287 cap0.40`): `3.30756 @2850`.
  - `ap-EY4AwEODxLRRStI4t4IN60` (`3000 linear capwin040 2400-3000`): `3.31710 @2775`.
  - `ap-4au2IK8zcJNStwy4edfPwt` (`3000 linear no-LocoProp post2400`): `3.32564 @2700`.
  - `ap-dqkxpnQ5w54UhjBDWmwbvF` (`3000 PR287 no-LocoProp post2400`): `3.34847 @2525`.
  - `ap-2rie7tf5m8Dd90XGk6h90U` (`3000 linear floor0.04 no-LocoProp post2400 retry`): loaded at `3.37491 @2400`, waiting for post-resume validations.
  - `ap-DRieR7b1nuvh9QeZzA91P3` (`3100 cap-window full run`): `3.63504 @1000`.

Final/cleanup pass for this suffix family:

- The saved step-2800 checkpoint is present in Modal volume `nanogpt-speedrun-cache` at `track3_checkpoints/modal3100_locom_seed400_step2800.pt`; its validation loss was `3.320429563522339 @2800`.
- Direct continuation from the matched step-2400 checkpoint improved beyond the step-2800 checkpoint but did not hit target: `ap-dFrT1wOrSJtpVNdU6fhvtS` finished at `3.29214 @3100` (`3.29818 @3000`).
- Best 3000-deadline active-LocoProp suffixes also missed target:
  - `ap-BoBw1WtxypXNBUxBdY7XsO` (`fid3000-linear-cap020`): `3.29752 @3000`.
  - `ap-71kmMnKYH9SkULGzSRIjBq` (`s3000-pr2873065-cap020`): `3.29683 @3000`.
  - `ap-Ud1Jbwluq0wrdNV2HStcVW` (`s3000-pr2873065-cap040`): `3.29711 @3000`.
- Late cap window did not rescue the run: `ap-EY4AwEODxLRRStI4t4IN60` reached only `3.30167 @2925` before cleanup.
- No-LocoProp-after-2400 controls were behind the active suffixes: `ap-4au2IK8zcJNStwy4edfPwt` reached `3.30796 @2850`; `ap-dqkxpnQ5w54UhjBDWmwbvF` reached `3.32588 @2675`; `ap-2rie7tf5m8Dd90XGk6h90U` reached `3.34701 @2550`.
- Cleanup: stopped the remaining owned Track 3 suffix/full-run apps after they were no longer candidates for `3.28 <=3000/3100`: `ap-DRieR7b1nuvh9QeZzA91P3`, `ap-4au2IK8zcJNStwy4edfPwt`, `ap-Ud1Jbwluq0wrdNV2HStcVW`, `ap-EY4AwEODxLRRStI4t4IN60`, `ap-dqkxpnQ5w54UhjBDWmwbvF`, and `ap-2rie7tf5m8Dd90XGk6h90U`; `ap-71kmMnKYH9SkULGzSRIjBq`, `ap-BoBw1WtxypXNBUxBdY7XsO`, and `ap-dFrT1wOrSJtpVNdU6fhvtS` had already stopped. Did not touch unrelated `dw-pr` Modal apps.
- Decision: no n=8 fanout. This family beat the saved 2800 checkpoint loss but missed the PR confirmation target by roughly `0.012` at 3100 and `0.017` at 3000.

Correction/recovery: `ap-DRieR7b1nuvh9QeZzA91P3` was a standalone 3100 cap-window run, not just a spent suffix lane. It had reached `3.57186 @1250` when it was stopped, before the intended `1600-2400` `norm_cap=0.40` window. Relaunched the same standalone probe:

- App: `ap-2jVszraxi9ZJJG8r0sKWZD`.
- Run: `track3-simple-locom-3100-capwin040-1600-2400-h100-seed400-retry-20260601133820`.
- Function call: `fc-01KT1PGME1JYVDB1NH44HN32GM`.
- Setting: `TRACK3_TRAIN_STEPS=3100`, `TRACK3_SEED_OFFSET=400`, simple Track 3 source, `TRACK3_MBS=16`, LocoProp-M SGD all layers, `K=4`, `sample_tokens=1024`, base `norm_cap=0.20`, `TRACK3_LOCOM_NORM_CAP_WINDOWS=1600:2400:0.40`, `SCREEN_VAL_EVERY=125`.
- Local launch log: `.opencode/modal_track3-simple-locom-3100-capwin040-1600-2400-h100-seed400-retry-20260601133820.launch.log`.
- Launch verification: app active/detached on H100; generated `/tmp/train_gpt_simple_locoprop_m_3100.py`, `track3_trial_seed=400`, all 12 LocoProp layers owned. Next gate: verify `locoprop_m_apply step=1600` logs `cap=0.400`, then compare final `3000/3100` values against the missed suffix-family endpoints.
- Retry checks before the cap window: `4.64153 @125`, `4.11050 @250`, `3.93290 @375`, `3.82742 @500`, `3.75811 @625`, `3.71351 @750`, `3.67328 @875`, `3.63508 @1000`, `3.60727 @1125`, and `3.57265 @1250`, all with effective `cap=0.200`. This is essentially the original 3100 cap0.20 trajectory with small noise: slightly worse at `875`, slightly better at `1250` (`3.57351` original). The real test is the mid-run cap-window transition and the `2800/3000/3100` slope.

## 2026-06-01 What Went Off Around Step 2400/2800

The key observation is that the step-2400 resumed 3000-step schedules can be better than the original full-LocoProp 3100 run by step 2800, but they still flatten too high by step 3000.

| Variant | 2400 | 2500 | 2600 | 2700 | 2750 | 2800 | 2875 | 2925 | 3000/3100 | Read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Original full LocoProp 3100 cap0.20 | n/a | `3.35990` | n/a | n/a | `3.32528` | `3.31815` | `3.30966` | `3.30379` | `3.29672 @3000`, `3.29066 @3100` | Old reference. Good early state, weak terminal slope. |
| Replay checkpoint @2800 | n/a | n/a | n/a | n/a | n/a | `3.32043` | n/a | n/a | n/a | `+0.00228` worse than original @2800 before suffixes. |
| 2400 -> 3100 exact cap0.20 | `3.37491` | n/a | n/a | n/a | n/a | `3.31963` | `3.31132` | `3.30539` | `3.29818 @3000`, `3.29214 @3100` | Faithful resume; slightly worse than original at 2800/3100. |
| 2400 -> 3000 linear cap0.20 | `3.37491` | `3.35490` | `3.33985` | `3.32592` | `3.31976` | `3.31331` | `3.30578` | `3.30121` | `3.29752 @3000` | Helps @2800 by `-0.00484` vs original, but still flattens. |
| 2400 -> 3000 PR287 cap0.20 | `3.37491` | `3.35197` | `3.33677` | `3.32336` | `3.31752` | `3.31178` | `3.30510` | `3.30100` | `3.29683 @3000` | Best 3000 suffix. Helps @2800 by `-0.00637`, but final only `-0.00069` vs linear. |
| 2400 -> 3000 PR287 cap0.40 | `3.37491` | `3.35284` | `3.33715` | `3.32368` | `3.31800` | `3.31209` | `3.30545` | `3.30129` | `3.29711 @3000` | Higher cap is neutral/slightly worse than cap0.20. |
| 2400 -> 3000 linear cap0.40 window | `3.37491` | `3.35589` | `3.34050` | `3.32717` | `3.32034` | `3.31397` | `3.30637` | `3.30167` | stopped | Late cap boost did not help. |
| 2400 -> 3000 no-LocoProp post2400 | `3.37491` | `3.35466` | `3.33950` | `3.32564` | `3.31940` | `3.31304` | `3.30554` | n/a | stopped | Competitive through 2800, worse later; active LocoProp still helps a little late. |
| 2800 ckpt -> 3030 linear cap0.20 | n/a | n/a | n/a | n/a | n/a | `3.32043` | `3.30901` | `3.30337` | `3.29696 @3030` | Starting suffix at 2800 is too late and begins from worse state. |
| 2800 ckpt -> 3030 PR287 cap0.20 | n/a | n/a | n/a | n/a | n/a | `3.32043` | `3.30783` | `3.30286` | `3.29725 @3025` | PR287 helps slope slightly but still misses. |
| 2800 ckpt -> 3100 no-late | n/a | n/a | n/a | n/a | n/a | `3.32043` | `3.31192` | `3.30589` | `3.29267 @3100` | No-late at 2800 is not enough. |

Current synthesis:

- What helps: re-scheduling from step 2400 helps the state at 2800. The best evidence is PR287 cap0.20 reaching `3.31178 @2800`, about `0.00637` better than the original full-LocoProp `3.31815 @2800`.
- What does not help enough: none of the 2400 variants preserve enough terminal slope. The best 3000 endpoint is still only `3.29683`, so the improvement by 2800 mostly gets spent before target.
- What is actively bad: power tails and aggressive LR floors from the checkpoint; they spike or degrade early. Higher LocoProp cap (`0.40`) is neutral-to-worse in the tested late windows.
- What is ambiguous: disabling LocoProp after 2400 is competitive through 2800 but loses later; this suggests LocoProp is not simply poison after 2400, but the active correction is too weak/misaligned to solve the final slope problem.
- Practical implication: the bottleneck is not only "get a better 2800 point." We have a better 2800 point and still miss. The lever needs to improve the post-2800 descent rate, likely by changing the late optimizer/schedule shape rather than increasing LocoProp cap or flooring LR.

## 2026-06-01 PR287-to-Linear Hybrid Suffixes

Hypothesis: the PR287 cap0.20 suffix bought the best `2400 -> 2800` state (`3.31178 @2800`) but had weak `2800 -> 3000` descent. Test whether we can keep PR287's mid-run state and switch back to the original linear-3100 landing shape before the terminal segment.

Added a narrow LR schedule-switch knob:

- Commit: `cb707b1` (`Add Track 3 LR schedule switch`).
- Env: `TRACK3_LR_SWITCH_STEP`, `TRACK3_LR_AFTER_SWITCH`, `TRACK3_LR_AFTER_SWITCH_POWER`, `TRACK3_LR_AFTER_SWITCH_STEPS`.
- Smoke: generated and compiled a script with `TRACK3_LR_SCHEDULE=pr287`, `TRACK3_LR_SCHEDULE_STEPS=3065`, `TRACK3_LR_SWITCH_STEP=2800`, `TRACK3_LR_AFTER_SWITCH=linear`, `TRACK3_LR_AFTER_SWITCH_STEPS=3100`. The generated `set_hparams` uses PR287 before the switch and linear progress against `schedule_steps=3100` after the switch.

Launched two H100 Modal suffixes from the matched step-2400 checkpoint:

| Variant | App | Function call | Switch | Latest | Read |
| --- | --- | --- | ---: | ---: | --- |
| PR287 -> linear3100 | `ap-tnTIbbdQSW4kj4IGHP9cQy` | `fc-01KT1S5DWTW9GT8EJA71V8WAFQ` | `2800` | stopped after `3.31246 @2850` | Reached PR287-quality `3.31175 @2800`, then immediately bumped to `3.31331 @2825` and collapsed to original-3100 parity by `2850`. |
| PR287 -> linear3100 | `ap-P1kAN6Y7xAKoMerGsF1lmn` | `fc-01KT1S9JEAHE1K6ZY78WG24CYY` | `2750` | stopped after `3.31557 @2825` | Switching earlier erased the PR287 advantage even faster: `3.31751 @2750`, `3.31736 @2800`, roughly original-3100 parity. |

Both used `TRACK3_LOCOM_NORM_CAP=0.20` and no LocoProp cap window. Decision: stopped both hybrid suffix apps. The direct "PR287 into original-linear tail" idea does not preserve the PR287 state; the switch creates a discontinuity / loss bump and returns the run to original-3100 pace within 25-50 steps. This says the lost terminal slope is not recovered by a hard schedule handoff.

## 2026-06-01 K5 500-Step Screens

User question: the earlier paper-faithful RMSProp path used `K=10`; try `K=5`, and check whether SGD LocoProp-M had ever been tested with `K=5`.

Local audit before launch:

- No completed/simple Track 3 SGD LocoProp-M `K=5` run found in the launch logs or experiment ledger.
- Confirmed simple Track 3 SGD LocoProp-M evidence was `K=4`; confirmed paper-faithful RMSProp probes were `K=10`.
- Added and pushed commit `cd3c730` (`Add Track 3 LocoProp-M local solve guards`) before launching:
  - `TRACK3_LOCOM_NORM_TARGET`
  - `TRACK3_LOCOM_RMS_RESET_EACH_STEP`
  - `TRACK3_LOCOM_REQUIRE_LOSS_DECREASE`
  - `TRACK3_LOCOM_MIN_COS_DESC`
  - diagnostics now log `accepted=`.

Launched two Modal H100 500-step screens:

| Variant | App | Function call | Setting | Early read |
| --- | --- | --- | --- | --- |
| SGD `K=5` | `ap-Y1Ojg5JPG0Pf5l4KWynP3H` | `fc-01KT1W7SV5ZFF6F6PCWAYN8XVG` | simple Track 3, seed `2600`, `TRACK3_LOCOM_LOCAL_OPT=sgd`, `TRACK3_LOCOM_STEPS=5`, `inner_lr=0.1`, cap `0.20`, `SCREEN_VAL_EVERY=25` | `5.99019 @25`, `5.43137 @50`, `5.06952 @75`, `4.82865 @100`, `4.62684 @125`, `4.45742 @150`, `4.31892 @175`, `4.22076 @200`, `4.13426 @225`, `4.07291 @250`. Raw local solve is very large: at step 50 one logged layer has `lossK=2.685e+07`, `corr_norm=1.020e+05`, and cap scale `3.803e-06`; at step 100 one logged layer still has `lossK=2.100e+07`, `corr_norm=5.977e+04`. This is still a direction-preserving cap, but not a faithful local-solve magnitude. At the apples-to-apples 250 checkpoint, K5 is essentially tied/slightly worse than K4 (`4.07139`/`4.07186 @250`), so the step-125 edge did not convert into a clear rung. |
| RMSProp `K=5` gated/norm target | `ap-tGnZ4d65st5DLoldkt1OhI` | `fc-01KT1W7SY5KGTJS11J2QC33H28` | simple Track 3, seed `2700`, `TRACK3_LOCOM_LOCAL_OPT=rmsprop`, `TRACK3_LOCOM_STEPS=5`, start step `50`, `inner_lr=1e-5`, reset RMS state each step, require local loss decrease and `cos_desc >= 0`, norm target/cap `0.20`, `SCREEN_VAL_EVERY=25` | `6.01006 @25`, `5.45453 @50`, `5.08487 @75`, `4.86343 @100`, `4.68219 @125` (stopped after this; worse than SGD K5 and worse than the useful K4 SGD band). At step 50, local updates are sane but sparse under guards: logged layers `accepted=1/4`; by steps 75/100 this improved to `accepted=3/4`. Accepted corrections remain weakly aligned (`cos_desc` around `0.004-0.007`) and are normalized up to the `0.20` target when below scale. |

Active alongside this:

- The standalone 3100 cap-window retry `ap-2jVszraxi9ZJJG8r0sKWZD` crossed the intended window; `locoprop_m_apply step=1600` logs `cap=0.400`.
- Latest observed values: `3.51614 @1500`, `3.50194 @1625`, `3.47640 @1750`, `3.45552 @1875`; latest train step in the last poll was `1919`.


Follow-up launch after the gated RMSProp result underperformed:

- Stopped `ap-tGnZ4d65st5DLoldkt1OhI` at `4.68219 @125`.
- Launched ungated RMSProp K5 with the same reset/norm-target settings but without local-loss/cosine rejection:
  - App: `ap-RdIBDBTFfllEfRYqv8otW1`.
  - Function call: `fc-01KT1X00SWH8KZ31KK990XDARC`.
  - Run: `track3-simple-locom-rmsprop-k5-nogate-norm-500-h100-seed2800-20260601153132`.
  - Latest poll: `6.01066 @25`, `5.45736 @50`, `5.09321 @75`; mechanically clean but still slower than SGD K5 and the old K4 screen.

## 2026-06-01 3000-Scale Plot And Better-Base Lanes

Generated benchmark-scale plots for the ongoing 3000-ish Track 3 runs:

- `.opencode/plots/track3_3000ish_benchmark_scale.png`
- `.opencode/plots/track3_3000ish_benchmark_scale.svg`
- `.opencode/plots/track3_3000ish_late_zoom.png`
- `.opencode/plots/track3_3000ish_late_zoom.svg`
- `.opencode/plots/track3_3000ish_curves.tsv`

The visible failure mode is still the terminal taper: several variants are competitive through `~2800`, then do not keep enough `2800 -> 3000/3100` slope to reach `3.28`.

Conditional run launched after the cap-window lane failed its step-2500 gate:

- App: `ap-OEZ4y8NHM65HsYpn54m1hs`.
- Function call: `fc-01KT1ZNGB7WGZ13NC4DFZ68ZM2`.
- Run: `track3-simple-locom-3100-nolate1600-pr2871600-h100-seed2900-20260601161815`.
- Setting: simple Track 3 source, `TRACK3_TRAIN_STEPS=3100`, `TRACK3_SEED_OFFSET=2900`, LocoProp-M SGD `K=4`, cap `0.20`, `TRACK3_LOCOM_END_STEP=1600`, then `TRACK3_LR_SWITCH_STEP=1600`, `TRACK3_LR_AFTER_SWITCH=pr287`, `TRACK3_LR_AFTER_SWITCH_POWER=1.2`, `TRACK3_LR_AFTER_SWITCH_STEPS=3065`.
- Early gate: `4.64611 @125`; latest poll in this pass had trained through step `250` and was waiting for the step-250 validation print.
- Launch log: `.opencode/modal_track3-simple-locom-3100-nolate1600-pr2871600-h100-seed2900-20260601161815.launch.log`.

User asked for the simplest better-base compositions, both on a 3100 schedule. Added generator support for single-run self-contained Track 3 result logs so the #9 Skylight/update-clamp source can be used directly as `TRACK3_SOURCE`.

Launched two H100 Modal lanes using `records/track_3_optimization/results/20260501_skylight001/f78af80a-2ba3-4cf7-b9f7-e6e56ff2c54d.txt` as source:

| Variant | App | Function call | Setting | Initial read |
| --- | --- | --- | --- | --- |
| Skylight/update-clamp + LocoProp-M | `ap-E5pEDDsZLAx1VPP6SRcXI5` | `fc-01KT20H1MR3PH5NEQ15ZVNG7BT` | `TRACK3_TRAIN_STEPS=3100`, seed `3001`, `TRACK3_LR_SCHEDULE=linear`, LocoProp-M SGD `K=4`, cap `0.20` | Active. `track3_trial_seed=3001`; all 12 layers owned. At step 10, `base_step` is about `2.08`, confirming this is the Skylight/update-clamp substrate rather than the simple Muon base. |
| Skylight/update-clamp + LocoProp-M + power LR | `ap-URsRlj7MQpd1CthhhB4286` | `fc-01KT20KJ3BMBXY73F1PHKY603S` | same source/settings, seed `3002`, `TRACK3_LR_SCHEDULE=power`, `TRACK3_LR_POWER=0.5` | Active. Printed initial `10.82580 @0`; waiting for first post-boot gate. |

Local launch logs:

- `.opencode/modal_track3-skylight-locom-3100-linear-h100-seed3001-20260601163308.launch.log`
- `.opencode/modal_track3-skylight-locom-3100-power05-h100-seed3002-20260601163440.launch.log`

Next gates:

- Stop either Skylight lane early if the step-125/250 band is clearly bad relative to #9 and the simple LocoProp reference.
- If either Skylight lane remains healthy into the mid-run and fixes the late taper, promote to a 3000/3030 schedule before starting n=8.

Follow-up after 125/250 gates:

- Existing simple no-late1600/PR2871600 lane: `4.64611 @125`, `4.11183 @250`, `3.92924 @375`, `3.82259 @500`.
- Skylight/update-clamp + LocoProp-M linear 3100: `4.63381 @125`, `4.09934 @250`. This is materially ahead of both published #9 (`4.65573 @125`, `4.11008 @250`) and the simple-current lane at the same steps.
- Skylight/update-clamp + LocoProp-M power0.5 3100: `4.63269 @125`, `4.09424 @250`. This is the strongest early lane so far.

Because both better-base lanes cleared the 250 gate, launched matching 3000 schedules:

| Variant | App | Function call | Setting | Launch log |
| --- | --- | --- | --- | --- |
| Skylight/update-clamp + LocoProp-M 3000 linear | `ap-iJqNtIaMH3U3og8enGykdS` | `fc-01KT21NNWWSFFE3FR15M901KSW` | `TRACK3_TRAIN_STEPS=3000`, seed `3003`, linear LR, LocoProp-M SGD `K=4`, cap `0.20` | `.opencode/modal_track3-skylight-locom-3000-linear-h100-seed3003-20260601165232.launch.log` |
| Skylight/update-clamp + LocoProp-M 3000 power0.5 | `ap-JyuQA5cyxmoa1ikZ0V1Db1` | `fc-01KT21QT8Q583TM48J88T0CNVP` | `TRACK3_TRAIN_STEPS=3000`, seed `3004`, `TRACK3_LR_SCHEDULE=power`, `TRACK3_LR_POWER=0.5`, LocoProp-M SGD `K=4`, cap `0.20` | `.opencode/modal_track3-skylight-locom-3000-power05-h100-seed3004-20260601165428.launch.log` |

Next decision gates:

- Keep the 3100 Skylight lanes through at least `500`; if they keep the advantage, monitor to cooldown and final taper.
- Check 3000 lanes at `125/250`; if they match the 3100 early advantage, continue them and consider additional seeds only after mid-run evidence, not just the first 250 steps.

Follow-up decisions:

- Stopped the two 3100 Skylight lanes after their early advantage faded by step 500:
  - `ap-E5pEDDsZLAx1VPP6SRcXI5` linear 3100: `4.63381 @125`, `4.09934 @250`, `3.93439 @375`, `3.84158 @500`.
  - `ap-URsRlj7MQpd1CthhhB4286` power0.5 3100: `4.63269 @125`, `4.09424 @250`, `3.92877 @375`, `3.84584 @500`.
  - Comparison lane `ap-OEZ4y8NHM65HsYpn54m1hs` simple no-late1600/PR2871600: `3.82259 @500`, so the Skylight/update-clamp composition was not competitive on the 3100 persistence read.
- Kept the two 3000 Skylight probes because they cleared the 250 gate:
  - `ap-iJqNtIaMH3U3og8enGykdS` 3000 linear: `4.59035 @125`, `4.08768 @250`.
  - `ap-JyuQA5cyxmoa1ikZ0V1Db1` 3000 power0.5: `4.60784 @125`, `4.09095 @250`.
- Because 3000 linear is the lead, launched three more 3000-linear seeds:

| Seed | App | Function call | Launch log |
| ---: | --- | --- | --- |
| `3005` | `ap-Fabx46LTrIpepEMsJQT9j0` | `fc-01KT22V8TVHQV69REVG1107GC3` | `.opencode/modal_track3-skylight-locom-3000-linear-h100-seed3005-20260601171351.launch.log` |
| `3006` | `ap-D4hTs8CYlcuvhPgElF9RSO` | `fc-01KT22VYX0E4W9C4J0H68JKK9M` | `.opencode/modal_track3-skylight-locom-3000-linear-h100-seed3006-20260601171414.launch.log` |
| `3007` | `ap-RRhQ6HgNpP3Ojmm0DOo75e` | `fc-01KT22WMV9KT6CVSYGFPGK9ESD` | `.opencode/modal_track3-skylight-locom-3000-linear-h100-seed3007-20260601171437.launch.log` |

Active owned H100 set after cleanup/fanout: simple conditional 3100 (`ap-OEZ4y8NHM65HsYpn54m1hs`), initial 3000 linear (`ap-iJqNtIaMH3U3og8enGykdS`), initial 3000 power0.5 (`ap-JyuQA5cyxmoa1ikZ0V1Db1`), and linear fanout seeds `3005-3007`.

500-gate cleanup:

- Initial 3000 probes did not preserve their early advantage:
  - `ap-iJqNtIaMH3U3og8enGykdS` 3000 linear seed3003: `4.59035 @125`, `4.08768 @250`, `3.92546 @375`, `3.84428 @500`.
  - `ap-JyuQA5cyxmoa1ikZ0V1Db1` 3000 power0.5 seed3004: `4.60784 @125`, `4.09095 @250`, `3.92932 @375`, `3.84589 @500`.
  - Simple conditional comparison `ap-OEZ4y8NHM65HsYpn54m1hs`: `3.82259 @500`.
- Fanout seed 125s were good but not enough to override the failed 500 persistence check:
  - seed3005: `4.62177 @125`.
  - seed3006: `4.61294 @125`.
  - seed3007: `4.61623 @125`.
- Stopped all five 3000 Skylight probes after this 500 gate: `ap-iJqNtIaMH3U3og8enGykdS`, `ap-JyuQA5cyxmoa1ikZ0V1Db1`, `ap-Fabx46LTrIpepEMsJQT9j0`, `ap-D4hTs8CYlcuvhPgElF9RSO`, `ap-RRhQ6HgNpP3Ojmm0DOo75e`.
- Current active owned H100 set after cleanup: only `ap-OEZ4y8NHM65HsYpn54m1hs`, the simple no-LocoProp-after-1600 plus PR287-after-1600 conditional run. It has reached `3.63361 @1000`; next meaningful gate is the `1600` switch and following `1625/1750` behavior.

Interim poll for the active conditional lane:

- `ap-OEZ4y8NHM65HsYpn54m1hs`: `3.57134 @1250`, latest train step `1263`, step average about `3633ms`.
- This is still slightly ahead of the earlier 3100 seed-400 trajectory around `1250`, so the run remains worth carrying to the switch.
- No new fanout yet. The actual decision gate is the post-switch `1625/1750` behavior after LocoProp stops at `1600` and the PR287-style schedule takes over.

Switch-gate follow-up:

- Same app: `3.54476 @1375`, `3.51805 @1500`, `3.49718 @1625`; latest train step after the poll was `1641`.
- No `locoprop_m_apply step=1600` line was present in the polled logs, consistent with `TRACK3_LOCOM_END_STEP=1600` using `step < end_step`.
- The `1625` read is better than the old 8x LocoProp-M target run (`3.50672 @1625`) and better than the cap-window retry (`3.50194 @1625`), so it clears the "encouraging 3100" gate.

Launched one compressed schedule probe with the same primitive:

| Variant | App | Function call | Setting | Launch log |
| --- | --- | --- | --- | --- |
| simple LocoProp-M to 1600, PR287-after-1600, 3000 steps | `ap-QNwyCxb4P3PyxhCfUtvAYU` | `fc-01KT25SH951PZBZX74MJSGCR9K` | `TRACK3_TRAIN_STEPS=3000`, seed `3100`, `TRACK3_LOCOM_END_STEP=1600`, `TRACK3_LR_SWITCH_STEP=1600`, `TRACK3_LR_AFTER_SWITCH=pr287`, `TRACK3_LR_AFTER_SWITCH_POWER=1.2`, `TRACK3_LR_AFTER_SWITCH_STEPS=3065` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2871600-h100-seed3100-20260601180518.launch.log` |

Next gates: keep the 3100 lane to at least `1750`; use the 3000 lane's `125/250/500` reads only as early sanity checks, and do not fan out until the compressed schedule preserves the mid-run/late-run advantage.

Follow-up:

- `ap-OEZ4y8NHM65HsYpn54m1hs` reached `3.47255 @1750`; latest train step was `1811`.
- This is better than the old 8x LocoProp-M target run (`3.48503 @1750`) and the cap-window retry (`3.47640 @1750`), so the no-LocoProp-after-1600 / PR287-after-1600 handoff remains hot through the first two post-switch validations.
- `ap-QNwyCxb4P3PyxhCfUtvAYU` 3000-step probe reached `4.63156 @125`; launch/config is clean and early loss is not an immediate rejection, but the real gate remains `500+`.

Launched one 3030 companion to test the preferred sub-3100 window without a broad fanout yet:

| Variant | App | Function call | Setting | Launch log |
| --- | --- | --- | --- | --- |
| simple LocoProp-M to 1600, PR287-after-1600, 3030 steps | `ap-XbZFPuvUtrs8Ug3NKCL9Rp` | `fc-01KT26CGRAQMJZM6YZDZBTNC8E` | `TRACK3_TRAIN_STEPS=3030`, seed `3101`, `TRACK3_LOCOM_END_STEP=1600`, `TRACK3_LR_SWITCH_STEP=1600`, `TRACK3_LR_AFTER_SWITCH=pr287`, `TRACK3_LR_AFTER_SWITCH_POWER=1.2`, `TRACK3_LR_AFTER_SWITCH_STEPS=3065` | `.opencode/modal_track3-simple-locom-3030-nolate1600-pr2871600-h100-seed3101-20260601181542.launch.log` |

Active owned Modal H100s after this launch: `ap-OEZ4y8NHM65HsYpn54m1hs` (3100), `ap-QNwyCxb4P3PyxhCfUtvAYU` (3000), `ap-XbZFPuvUtrs8Ug3NKCL9Rp` (3030). Do not start n=8 until 3000/3030 preserve the signal at least through the `500` gate.

Next poll:

- `ap-OEZ4y8NHM65HsYpn54m1hs` (3100): `3.44775 @1875`, latest train step `1990`. This remains stronger than the cap-window retry at the same region (`3.45552 @1875`) and continues to support the handoff hypothesis.
- `ap-QNwyCxb4P3PyxhCfUtvAYU` (3000): `4.63156 @125`, `4.10962 @250`, latest train step `316`. This is sane enough to continue, but still only an early screen.
- `ap-XbZFPuvUtrs8Ug3NKCL9Rp` (3030): `4.64947 @125`, latest train step `141`. Weak first point versus the 3000 probe but not enough to reject.
- Decision: no broad fanout yet. Wait for the 3000 `500` gate and the 3030 `250/500` gates.

Next poll:

- `ap-OEZ4y8NHM65HsYpn54m1hs` (3100): `3.42485 @2000`, latest train step `2123`; still ahead of the prior 3100/cap-window family in this region.
- `ap-QNwyCxb4P3PyxhCfUtvAYU` (3000): `4.63156 @125`, `4.10962 @250`, `3.93135 @375`, latest train step `448`. Slightly behind the active 3100 lane at the same early point but still plausible.
- `ap-XbZFPuvUtrs8Ug3NKCL9Rp` (3030): `4.64947 @125`, `4.12058 @250`, latest train step `265`. This seed remains weaker.
- Decision unchanged: wait for the 3000 `500` gate before any broad fanout.

500 gate check:

- `ap-OEZ4y8NHM65HsYpn54m1hs` (3100): `3.40419 @2125`, latest train step `2225`. This is materially ahead of the earlier original-3100/replay family around this region, so the 3100 schedule remains the lead diagnostic.
- `ap-QNwyCxb4P3PyxhCfUtvAYU` (3000): `3.82744 @500`, latest train step `549`. This does not clear the fanout gate: it is slightly worse than the same active 3100 lane at `500` (`3.82259`) and only roughly comparable to older cap0.20 3100 screens.
- `ap-XbZFPuvUtrs8Ug3NKCL9Rp` (3030): still only `4.64947 @125`, `4.12058 @250`, latest train step `368`; continue to `500` before judging.
- Decision: no n=8 fanout yet. Keep all three running; use the 3100 lane as the hot schedule diagnostic, and wait for compressed lanes to prove late/mid-run persistence before expanding.

The 3100 lane continued to strengthen:

- `ap-OEZ4y8NHM65HsYpn54m1hs` (3100): `3.38332 @2250`, `3.36462 @2375`, latest train step `2383`.
- This is substantially ahead of the old original-3100/cap0.20 family in the same region and now plausible to reach `3.28` around or before step `3000`.

Compressed lanes at the same poll:

- `ap-QNwyCxb4P3PyxhCfUtvAYU` (3000): `3.75798 @625`, latest train step `713`; still close to but not better than the 3100 lead seed's early curve.
- `ap-XbZFPuvUtrs8Ug3NKCL9Rp` (3030): `3.92984 @375`, `3.82815 @500`, latest train step `514`; recovered from the weak first point but did not clear a fanout gate.

Decision: launch a small 3100 replication fanout, not full n=8 yet. Rationale: the 3100 schedule is the first variant with a persistent post-switch lead into the `2250-2375` range, while 3000/3030 are only comparable early.

| Seed | App | Function call | Setting | Launch log |
| ---: | --- | --- | --- | --- |
| `3200` | `ap-67AzRw0vPZsWuE9TWupFfS` | `fc-01KT28FY8QMPZ514B6KX2QV29H` | `TRACK3_TRAIN_STEPS=3100`, `TRACK3_LOCOM_END_STEP=1600`, `TRACK3_LR_SWITCH_STEP=1600`, `TRACK3_LR_AFTER_SWITCH=pr287`, `TRACK3_LR_AFTER_SWITCH_POWER=1.2`, `TRACK3_LR_AFTER_SWITCH_STEPS=3065` | `.opencode/modal_track3-simple-locom-3100-nolate1600-pr2871600-h100-seed3200-20260601185228.launch.log` |
| `3201` | `ap-cdEz3MSGQZs2V3nFTfFHRh` | `fc-01KT28GP71K3W750Y9QMYJM325` | same | `.opencode/modal_track3-simple-locom-3100-nolate1600-pr2871600-h100-seed3201-20260601185254.launch.log` |
| `3202` | `ap-F2xU6KVgg2wA5yMPTIXzkU` | `fc-01KT28HDHW09783ZPVAM2V98YV` | same | `.opencode/modal_track3-simple-locom-3100-nolate1600-pr2871600-h100-seed3202-20260601185319.launch.log` |
| `3203` | `ap-vH5zZgiIoWiqvCPMSOsL1m` | `fc-01KT28J40D7EEQPJ7G5HVTGJEH` | same | `.opencode/modal_track3-simple-locom-3100-nolate1600-pr2871600-h100-seed3203-20260601185343.launch.log` |

Active owned Modal H100s after this fanout: 3100 lead `2900`, compressed `3000/3030`, and 3100 replicas `3200-3203` (`7` total tasks). Next action: gate replicas at `125/250/500`, continue lead seed to `2500/2750/3000`, and only launch the remaining n=8 replicas if the first replica batch tracks.

Status after user asked what the current 3100 run is:

- Lead `ap-OEZ4y8NHM65HsYpn54m1hs`: `3.34646 @2500`, latest train step `2526`.
- This run is not plain simple Muon + LocoProp-M through the whole schedule. It is simple Track 3 plus LocoProp-M only until `1600`, then `TRACK3_LR_AFTER_SWITCH=pr287` with `TRACK3_LR_AFTER_SWITCH_POWER=1.2`.
- Compressed probes:
  - 3000 `ap-QNwyCxb4P3PyxhCfUtvAYU`: `3.71154 @750`, latest train step `855`.
  - 3030 `ap-XbZFPuvUtrs8Ug3NKCL9Rp`: `3.75738 @625`, latest train step `649`.
- 3100 replicas `3200-3203` were alive but had not hit first validation yet; latest train steps were roughly `102-114`.
- Decision: keep waiting for replica `125/250/500` gates. Do not launch additional H100s before the replica batch produces real validation points.

Replica first gate:

| Seed | App | Latest | Val @125 |
| ---: | --- | ---: | ---: |
| `3200` | `ap-67AzRw0vPZsWuE9TWupFfS` | `176` | `4.64016` |
| `3201` | `ap-cdEz3MSGQZs2V3nFTfFHRh` | `180` | `4.63922` |
| `3202` | `ap-F2xU6KVgg2wA5yMPTIXzkU` | `175` | `4.63887` |
| `3203` | `ap-vH5zZgiIoWiqvCPMSOsL1m` | `167` | `4.64363` |

Read: all four replicas are in a tight normal band at `125`, so keep them to `250/500`. Still no final n=8 expansion until the batch clears stronger gates.

Replica second gate and n=8 expansion:

- Lead `ap-OEZ4y8NHM65HsYpn54m1hs`: `3.32907 @2625`, latest train step `2728`.
- Compressed probes:
  - 3000 `ap-QNwyCxb4P3PyxhCfUtvAYU`: `3.63195 @1000`, latest train step `1050`.
  - 3030 `ap-XbZFPuvUtrs8Ug3NKCL9Rp`: `3.71212 @750`, latest train step `839`.
- First replica batch at `250`:
  - seed `3200`: `4.11099 @250`.
  - seed `3201`: `4.10869 @250`.
  - seed `3202`: `4.10772 @250`.
  - seed `3203`: `4.11173 @250`.

The first replica batch remains tight and normal through `250`. Because the lead seed is still strongly ahead late and the first replica batch is not showing early instability, launch the remaining three 3100 replicas needed to have `n=8` in flight.

| Seed | App | Function call | Setting | Launch log |
| ---: | --- | --- | --- | --- |
| `3300` | `ap-TrGV7ckITWd9UNSZJkYjbM` | `fc-01KT29Q9M4CWV53P8YT7N07RBE` | `TRACK3_TRAIN_STEPS=3100`, `TRACK3_LOCOM_END_STEP=1600`, `TRACK3_LR_SWITCH_STEP=1600`, `TRACK3_LR_AFTER_SWITCH=pr287`, `TRACK3_LR_AFTER_SWITCH_POWER=1.2`, `TRACK3_LR_AFTER_SWITCH_STEPS=3065` | `.opencode/modal_track3-simple-locom-3100-nolate1600-pr2871600-h100-seed3300-20260601191356.launch.log` |
| `3301` | `ap-YaeWjvWuZJFynKErPXip71` | `fc-01KT29R2ST8HDKDAPXMN77TKF8` | same | `.opencode/modal_track3-simple-locom-3100-nolate1600-pr2871600-h100-seed3301-20260601191424.launch.log` |
| `3302` | `ap-oVsGiCijivr3kzcFlziFdM` | `fc-01KT29RSWZ40W3S02XWH0R9M2A` | same | `.opencode/modal_track3-simple-locom-3100-nolate1600-pr2871600-h100-seed3302-20260601191450.launch.log` |

Active owned Modal H100s after launch: ten tasks total: eight 3100 schedule seeds (`2900`, `3200-3203`, `3300-3302`) plus 3000/3030 probes (`3100`, `3101`). Next gate: first batch `500`, second batch `125/250`, and lead seed `2750/2875/3000`.

Lead late checkpoint and first replica batch `375`:

- Lead `ap-OEZ4y8NHM65HsYpn54m1hs`: `3.31391 @2750`, `3.30849 @2800`, latest train step `2824`.
- This remains ahead of the old original full-LocoProp 3100 cap0.20 reference (`3.32528 @2750`, `3.31815 @2800`), but it still needs roughly `0.0285` improvement over the next 200 steps to hit `3.28 @3000`.
- First replica batch:
  - seed `3200`: `3.92715 @375`.
  - seed `3201`: `3.93429 @375`.
  - seed `3202`: `3.92899 @375`.
  - seed `3203`: `3.92758 @375`.
- Read: replicas remain broadly normal through `375`, with seed `3201` slightly weaker. Continue to the `500` gate; do not stop anything yet.

Lead `2875/2900` and partial first-replica `500` gate:

- Lead `ap-OEZ4y8NHM65HsYpn54m1hs`: `3.30185 @2875`, `3.29978 @2900`, latest train step `2902`.
- This is still ahead of old 3100 baselines, but not on pace for `3.28 @3000`; it is currently more plausible as a `3100` candidate than a sub-3000 candidate.
- First replica batch:
  - seed `3201`: `3.82576 @500`.
  - seed `3202`: `3.82843 @500`.
  - seeds `3200` and `3203` were right at the `500` boundary and had not printed the `500` val in this poll.
- Decision: keep all active lanes. Do not start more; n=8 is already in flight for the 3100 schedule, and the key question is now whether enough seeds hit `3.28` by `3100`.

User asked whether a 3000 end-schedule run was launched for this primitive:

- Yes: `ap-QNwyCxb4P3PyxhCfUtvAYU`, seed `3100`, `TRACK3_TRAIN_STEPS=3000`, same `TRACK3_LOCOM_END_STEP=1600` and `TRACK3_LR_AFTER_SWITCH=pr287` handoff.
- Latest: `3.56967 @1250/3000`, latest train step `1289`. It is close to the 3100 lead's early curve but not outperforming.
- The 3100 lead at the same poll was `3.29786 @2925/3100`, latest train step `2939`; still above target, with the decisive `3000/3100` prints pending.

Schedule-horizon note after inspecting WR scripts:

- Older/simple Track 3 scripts tie LR progress to `train_steps`, so they land at zero LR at the run end.
- The PR287/Soft-Muon-style result decouples run length and LR horizon (`FINAL_TRAIN_STEPS=3040`, `FINAL_SCHEDULE_STEPS=3105`, power `1.2`), so the run ends while LR is still nonzero.
- Our 3100 switch run used `TRACK3_LR_AFTER_SWITCH_STEPS=3065`, so it begins landing to zero before the `3100` run end; the 3000 probe with the same horizon ends before zero.

Lead `3000` result:

- `ap-OEZ4y8NHM65HsYpn54m1hs`: `3.29374 @3000/3100`, latest train step `3018`.
- It missed `3.28 @3000` by about `0.0137`, so this is not a sub-3000 hit.

Launched one PR287-style horizon diagnostic, not a 3500 run:

| Variant | App | Function call | Setting | Launch log |
| --- | --- | --- | --- | --- |
| simple LocoProp-M to 1600, PR287-after-1600, 3040 steps with 3105 LR horizon | `ap-UFX7iAhRQvOQ5NmqWCkWlc` | `fc-01KT2AX88FEW73NTE94575FCK6` | `TRACK3_TRAIN_STEPS=3040`, seed `3400`, `TRACK3_LOCOM_END_STEP=1600`, `TRACK3_LR_SWITCH_STEP=1600`, `TRACK3_LR_AFTER_SWITCH=pr287`, `TRACK3_LR_AFTER_SWITCH_POWER=1.2`, `TRACK3_LR_AFTER_SWITCH_STEPS=3105` | `.opencode/modal_track3-simple-locom-3040-nolate1600-pr2873105-h100-seed3400-20260601193442.launch.log` |

Read: 3500 would be a slow upper-bound diagnostic, not the next speedrun move. The useful schedule question is whether PR287's nonzero-LR-at-end horizon fixes the last `0.014` without extending all the way to 3500.

## 2026-06-02 Active-Window LocoProp Re-On Probe

Added an explicit active-window knob for sampled LocoProp-M:

- Code: `TRACK3_LOCOM_ACTIVE_WINDOWS=start:end[,start:end...]`.
- Semantics: when nonempty, this overrides the single contiguous `TRACK3_LOCOM_START_STEP` / `TRACK3_LOCOM_END_STEP` predicate while preserving `TRACK3_LOCOM_INTERVAL`.
- Local validation: generated `/tmp/train_gpt_reon2800.py` with `TRACK3_LOCOM_ACTIVE_WINDOWS=0:1600,2800:3040`; `py_compile` passed and generated `_locom_active` contains the window predicate.

Launched one H100 Modal probe that turns LocoProp-M back on for the final taper:

| Variant | App | Function call | Setting | Launch log |
| --- | --- | --- | --- | --- |
| simple LocoProp-M `0:1600` and `2800:3040`, PR287-after-1600, 3040 steps with 3105 LR horizon | `ap-oJt8hUqjcUqyJINytpVyPR` | `fc-01KT2CE3E82J1C9H37YDNBZPW0` | `TRACK3_TRAIN_STEPS=3040`, seed `3401`, `TRACK3_LOCOM_ACTIVE_WINDOWS=0:1600,2800:3040`, `TRACK3_LR_SWITCH_STEP=1600`, `TRACK3_LR_AFTER_SWITCH=pr287`, `TRACK3_LR_AFTER_SWITCH_POWER=1.2`, `TRACK3_LR_AFTER_SWITCH_STEPS=3105` | `.opencode/modal_track3-simple-locom-3040-reon2800-pr2873105-h100-seed3401-20260601200114.launch.log` |

Launch verification:

- `modal app list` showed `ap-oJt8hUqjcUqyJINytpVyPR` alive as a detached app with one task.
- Remote logs confirmed `track3_trial_seed=3401`, all 12 LocoProp MLP `fc` layers owned, finite `10.82580 @0`, and nonzero capped corrections at step `2`.
- The decisive verification points are now:
  - no `locoprop_m_apply` at/after `1600` until the re-on point,
  - `locoprop_m_apply step=2800`,
  - compare `2800/2875/3000/3040` against the no-reon 3040 probe and the old 3100 lead.

Concurrent no-reon 3040 probe status:

- `ap-UFX7iAhRQvOQ5NmqWCkWlc`, seed `3400`, same 3040/3105 schedule but only `TRACK3_LOCOM_END_STEP=1600`, reached `4.11290 @250` with normal early LocoProp corrections.

Skylight/update-clamp plus LocoProp-M recap:

- This was the NorMuon/update-clamp substrate test using `records/track_3_optimization/results/20260501_skylight001/f78af80a-2ba3-4cf7-b9f7-e6e56ff2c54d.txt`.
- It was promising only at the first two gates:
  - 3100 linear: `4.63381 @125`, `4.09934 @250`.
  - 3100 power0.5: `4.63269 @125`, `4.09424 @250`.
  - Both beat the published #9 reference at those early gates.
- It faded by step `500`:
  - 3100 linear: `3.84158 @500`.
  - 3100 power0.5: `3.84584 @500`.
  - Simple conditional comparison was `3.82259 @500`.
- The 3000 Skylight fanout also faded by `500`, so all Skylight/update-clamp + LocoProp-M lanes were stopped. Current read: do not allocate the next runs to this composition unless we first find a schedule or active-window reason it should differ materially.

## 2026-06-02 Seed2900 Step-2500 Checkpoint Replays

User clarification: "the good lead seed" here means the recent best-performing seed from this round, not the older seed400 full-LocoProp run. The target trajectory is:

- seed `2900`,
- simple Track 3 source,
- LocoProp-M active only until step `1600`,
- PR287-style schedule after step `1600`,
- `TRACK3_LR_AFTER_SWITCH_POWER=1.2`,
- `TRACK3_LR_AFTER_SWITCH_STEPS=3065`.

Two mistaken seed400 checkpoint attempts were launched first and immediately stopped:

| Mistaken run | App | Function call | State |
| --- | --- | --- | --- |
| seed400 3100 checkpoint-at-2500 | `ap-kviZs5MiYPu6icSOdYSL69` | `fc-01KT2CK2ZTNG593CEYAVCAHG1D` | stopped after remote logs confirmed seed400 |
| seed400 3000 checkpoint-at-2500 | `ap-kWVq7yVtJ9cjET31v9j9ae` | `fc-01KT2CK2TEP7AXHTPHMYT672TM` | stopped after remote logs confirmed seed400 |

Launched the corrected seed2900 checkpoint replays:

| Schedule | App | Function call | Setting | Expected checkpoint | Launch log |
| --- | --- | --- | --- | --- | --- |
| 3100 | `ap-82jZGAorIouGJ2H084NIT8` | `fc-01KT2CNWK03RHEHNG8XN5CBPS7` | `TRACK3_TRAIN_STEPS=3100`, `TRACK3_SEED_OFFSET=2900`, `TRACK3_LOCOM_END_STEP=1600`, `TRACK3_LR_SWITCH_STEP=1600`, `TRACK3_LR_AFTER_SWITCH=pr287`, `TRACK3_LR_AFTER_SWITCH_POWER=1.2`, `TRACK3_LR_AFTER_SWITCH_STEPS=3065`, `TRACK3_CHECKPOINT_STEPS=2500`, `TRACK3_CHECKPOINT_EXIT_AFTER=1`, `TRACK3_TARGET_LOSS=0` | `/root/.cache/track3_checkpoints/modal3100_nolate1600_pr287_locom_seed2900_step2500.pt` | `.opencode/modal_track3-simple-locom-3100-nolate1600-pr287-ckpt2500-h100-seed2900-20260601200540.launch.log` |
| 3000 | `ap-aMJg05trVXsT8rfFsRkQne` | `fc-01KT2CNWJQ30TPFF3WAKZNF6FF` | same, but `TRACK3_TRAIN_STEPS=3000` and checkpoint prefix `modal3000_nolate1600_pr287_locom` | `/root/.cache/track3_checkpoints/modal3000_nolate1600_pr287_locom_seed2900_step2500.pt` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr287-ckpt2500-h100-seed2900-20260601200540.launch.log` |

Launch verification:

- `modal app list` showed both corrected apps alive as detached apps with one task each.
- Remote logs for both corrected apps confirmed `track3_trial_seed=2900`, generated train steps `3100` / `3000`, and all 12 LocoProp MLP `fc` layers owned.
- Next verification: wait for `track3_checkpoint_saved step:2500` in each app, then verify the two checkpoint files are present in Modal volume `nanogpt-speedrun-cache`.

Short follow-up:

- User asked whether a `3045` checkpoint-at-2500 replay was also running. It was not, so one was launched:
  - App: `ap-BM0MMyEr1SjCgCYugjmQfJ`.
  - Function call: `fc-01KT2D3ZT44KW0D5EATA41S363`.
  - Launch log: `.opencode/modal_track3-simple-locom-3045-nolate1600-pr287-ckpt2500-h100-seed2900-20260601201323.launch.log`.
  - Setting: seed `2900`, `TRACK3_TRAIN_STEPS=3045`, `TRACK3_LOCOM_END_STEP=1600`, PR287-after-1600, checkpoint at `2500`.
- User then clarified that the existing `3000` checkpoint replay is enough, so the `3045` app was stopped immediately. Remote logs confirmed seed `2900`, finite `10.82580 @0`, and stop around step `5`. Do not count the `3045` app as an active checkpoint lane or result.

Current live status after this correction:

- Active:
  - `ap-UFX7iAhRQvOQ5NmqWCkWlc`: 3040/no-reon seed3400, latest `3.82789 @500`.
  - `ap-oJt8hUqjcUqyJINytpVyPR`: 3040/reon2800 seed3401, latest `4.63290 @125`.
  - `ap-82jZGAorIouGJ2H084NIT8`: 3100 seed2900 checkpoint replay, latest `4.63302 @125`.
  - `ap-aMJg05trVXsT8rfFsRkQne`: 3000 seed2900 checkpoint replay, latest `4.63593 @125`.
- Stopped:
  - `ap-BM0MMyEr1SjCgCYugjmQfJ`: 3045 checkpoint replay, stopped by request.

Live poll update:

- Modal app list still shows exactly the four intended active detached Track 3 jobs: `ap-UFX7iAhRQvOQ5NmqWCkWlc`, `ap-oJt8hUqjcUqyJINytpVyPR`, `ap-82jZGAorIouGJ2H084NIT8`, and `ap-aMJg05trVXsT8rfFsRkQne`.
- The dropped 3045 replay `ap-BM0MMyEr1SjCgCYugjmQfJ` is stopped with zero tasks.
- Latest validation gates:
  - 3040/no-reon seed3400: `4.63536 @125`, `4.11290 @250`, `3.92771 @375`, `3.82789 @500`.
  - 3040/reon2800 seed3401: `4.63290 @125`, `4.10694 @250`.
  - 3100 seed2900 checkpoint replay: `4.63302 @125`; raw tail around step `214/3100`.
  - 3000 seed2900 checkpoint replay: `4.63593 @125`; raw tail around step `209/3000`.
- Modal volume `nanogpt-speedrun-cache` currently contains only the older seed400 checkpoint files: `track3_checkpoints/modal3100_locom_seed400_step2400.pt` and `track3_checkpoints/modal3100_locom_seed400_step2800.pt`. The two expected seed2900 step-2500 checkpoint files have not landed yet.
- Decision: no new fanout yet. The seed2900 replays are still too early, and the checkpoint array should wait for `track3_checkpoint_saved step:2500` plus volume-file verification.

Second live poll update:

- 3040/no-reon seed3400 reached `3.75703 @625`; this is not a breakout versus the old lead seed trajectory (`3.82259 @500`, `3.34646 @2500`, `3.29374 @3000`).
- 3100 seed2900 checkpoint replay reached `4.10655 @250`, better than the old lead's `4.11183 @250`.
- 3000 seed2900 checkpoint replay reached `4.10562 @250`, also better than the old lead's `4.11183 @250`.
- Decision: keep both seed2900 checkpoint lanes running. The `@250` screens are healthy enough to continue, but not enough to launch n=8 below-3000, since earlier 3000 schedules looked plausible early and then failed by the persistence gates. Next decision gates are `500/625` and then the actual `2500` checkpoint saves.

Third live poll update:

- Modal app list still shows exactly the four intended active detached H100 jobs; the dropped 3045 replay remains stopped.
- 3040/no-reon seed3400 has reached `3.60520 @1125`.
- 3040/reon2800 seed3401 has reached `3.67273 @875`.
- 3100 seed2900 checkpoint replay has reached `3.71145 @750`.
- 3000 seed2900 checkpoint replay has reached `3.71223 @750`.
- Old lead seed2900 reference was `3.75622 @625`, `3.71019 @750`, `3.63361 @1000`, `3.60412 @1125`, `3.34646 @2500`, and `3.29374 @3000`.
- Read: the active replays are effectively the same trajectory as the old lead so far, not a materially different or stronger signal. The 3000 checkpoint replay is close, but it is not a below-3000 fanout signal by itself.
- Modal volume `nanogpt-speedrun-cache` still contains only the older seed400 checkpoint files; the seed2900 step-2500 checkpoint files have not landed yet.
- Decision: do not launch n=8 or suffix arrays yet. Keep the four jobs alive for the step-2500 checkpoint saves and the late `2800+` re-on/no-reon comparison.

Fourth live poll update:

- Modal still shows the four intended active detached H100 jobs.
- 3040/no-reon seed3400 reached `3.57173 @1250` and `3.54420 @1375`.
- 3040/reon2800 seed3401 reached `3.63656 @1000`.
- 3100 seed2900 checkpoint replay reached `3.63220 @1000`.
- 3000 seed2900 checkpoint replay reached `3.63026 @1000`.
- Old lead seed2900 reference at the same region was `3.63361 @1000`, `3.60412 @1125`, and `3.57134 @1250`.
- Read: the checkpoint replays are healthy and maybe a few thousandths better than the old lead at `1000`, but still effectively the same trajectory. This is not enough by itself to justify below-3000 n=8 fanout, because the decisive failure mode is late landing near `2800-3100`.
- Decision: keep all four running. Wait for the step-2500 checkpoint saves and late-region comparisons.

Fifth live poll update:

- Modal app list still shows the four intended active detached H100 jobs.
- 3040/no-reon seed3400 reached `3.51522 @1500` and `3.49915 @1625`.
- 3040/reon2800 seed3401 reached `3.54448 @1375`.
- 3100 seed2900 checkpoint replay reached `3.57148 @1250`; raw tail around step `1325/3100`.
- 3000 seed2900 checkpoint replay reached `3.56812 @1250`; raw tail around step `1301/3000`.
- Old lead seed2900 reference at `1250` was `3.57134`, so the 3000 replay is about `0.0032` better there while the 3100 replay is effectively identical.
- Modal volume `nanogpt-speedrun-cache` still contains only the older seed400 checkpoint files; the seed2900 step-2500 checkpoints have not landed.
- Decision: continue the four runs. The 3000 replay is modestly encouraging but still below the threshold for n=8 below-3000 fanout; wait for `1500/1625` and then the step-2500 checkpoint saves.

Sixth live poll update, 2026-06-02 03:03 IST:

- Modal app list still shows exactly the four intended active detached H100 jobs:
  - `ap-UFX7iAhRQvOQ5NmqWCkWlc`: 3040/no-reon seed3400.
  - `ap-oJt8hUqjcUqyJINytpVyPR`: 3040/re-on-at-2800 seed3401.
  - `ap-82jZGAorIouGJ2H084NIT8`: 3100 seed2900 checkpoint replay.
  - `ap-aMJg05trVXsT8rfFsRkQne`: 3000 seed2900 checkpoint replay.
- Latest validation gates:
  - 3040/no-reon seed3400: `3.47748 @1750`; old seed2900 lead was `3.47255 @1750`, so this is worse by `0.00493`.
  - 3040/re-on-at-2800 seed3401: `3.54448 @1375`; old lead was `3.54476 @1375`, so this is effectively tied/slightly better by `0.00028`.
  - 3100 seed2900 checkpoint replay: `3.54403 @1375`; old lead was `3.54476 @1375`, slightly better by `0.00073`.
  - 3000 seed2900 checkpoint replay: latest validation remains `3.56812 @1250`; old lead was `3.57134 @1250`, better by `0.00322`, but the run has not yet produced the `1500/1625` persistence checks.
- Raw tails show current progress around:
  - 3040/no-reon: step `1768/3040`.
  - 3040/re-on-at-2800: step `1435/3040`.
  - 3100 replay: step `1375/3100`.
  - 3000 replay: step `1353/3000`.
- Modal volume still contains only the older seed400 checkpoints:
  - `track3_checkpoints/modal3100_locom_seed400_step2400.pt`
  - `track3_checkpoints/modal3100_locom_seed400_step2800.pt`
- Decision: no fanout yet. The current lanes are healthy but not materially ahead enough to launch n=8 below-3000. Keep monitoring for the 3000 replay's `1500/1625` gates and for seed2900 step-2500 checkpoint files.

Seventh live poll and fanout update, 2026-06-02 03:21 IST:

- The 3000 seed2900 checkpoint replay produced the first persistence gate strong enough to promote:
  - 3000 replay `ap-aMJg05trVXsT8rfFsRkQne`: `3.51147 @1500`.
  - Old seed2900 lead at `1500`: `3.51805`.
  - Delta: replay is better by `0.00658`.
- The same poll showed:
  - 3100 seed2900 checkpoint replay: `3.51599 @1500`, better than old lead by `0.00206`, but weaker than the 3000 replay.
  - 3040/re-on-at-2800 seed3401: `3.51455 @1500`, better than old lead by `0.00350`; its actual re-on-at-2800 hypothesis is not tested until late.
  - 3040/no-reon seed3400: `3.45426 @1875`; old lead was `3.44775 @1875`, so this lane was worse by `0.00651`.
- Decision: launch the full below-3000 confirmation wave. Important: the promising seed2900 3000 lane is a checkpoint replay with `TRACK3_CHECKPOINT_EXIT_AFTER=1`, so it will exit at step `2500` and cannot itself count as a full 3000 confirmation run.

Full 3000-step confirmation wave:

Common setting for all full confirmation seeds:

```text
TRACK3_TRAIN_STEPS=3000
TRACK3_LOCOM_END_STEP=1600
TRACK3_LR_SWITCH_STEP=1600
TRACK3_LR_AFTER_SWITCH=pr287
TRACK3_LR_AFTER_SWITCH_POWER=1.2
TRACK3_LR_AFTER_SWITCH_STEPS=3065
TRACK3_TARGET_LOSS=3.28
SCREEN_VAL_EVERY=25
NANOGPT_MODAL_GPU=H100
```

Confirmed active full 3000 lanes:

| Seed | App | Function call | Launch log |
| --- | --- | --- | --- |
| 3500 | `ap-j32hnOwCnt9M9uKKB72dlP` | `fc-01KT2J912RMQ26CEMWT4ZSJ8HY` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2873065-full-h100-seed3500-20260601214329.launch.log` |
| 3501 | `ap-NmxP7sV2WOjKj5hkG6t9A2` | `fc-01KT2J9QCTV14WG4MX7AM3ZYYS` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2873065-full-h100-seed3501-20260601214329.launch.log` |
| 3502 | `ap-GtJaJUQEKBK10mRwU2Fsws` | `fc-01KT2JADANTMMBWQCHM3G9JNZJ` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2873065-full-h100-seed3502-20260601214329.launch.log` |
| 3503 | `ap-muw1RIwCDZ6Zs12YqyCv97` | `fc-01KT2JB4P7NNEHD512KBAWDXWS` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2873065-full-h100-seed3503-20260601214329.launch.log` |
| 3504 | `ap-yFayRAOAoYZYIhZJtCuJDx` | `fc-01KT2JBVGVQSD85YXTER7FCFTM` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2873065-full-h100-seed3504-20260601214329.launch.log` |
| 3505 | `ap-oUdImgIQ5ybJoA00wfgcHN` | `fc-01KT2JCJZ4DB9DT6CGQVFNWXQ4` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2873065-full-h100-seed3505-20260601214329.launch.log` |
| 3508 | `ap-8hxb2L2CCcwndbsz2kdhcX` | `fc-01KT2JH4PY49SR0752K8YXATDW` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2873065-full-h100-seed3508-20260601214756.launch.log` |
| 3509 | `ap-uJtJvlUqQjK0e6S198WFhq` | `fc-01KT2JHVDV4MHZ8PZA1W5VQJSV` | `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2873065-full-h100-seed3509-20260601214756.launch.log` |

Verification:

- `modal app list` showed all eight full confirmation apps alive as detached apps with one task each.
- Logs confirmed seed IDs and finite `step:0/3000 val_loss:10.82580` for all eight full confirmation lanes.
- Modal appears effectively capped at ten live H100 tasks in this account/session. The first launch wave started six full lanes, while seed `3506` (`ap-ugRDej21Ml4vdugWDHuMPQ`) and seed `3507` (`ap-EMYwrk3lfa8FgHWphcjOv5`) came up as zero-task app shells.
- After stopping two lower-priority diagnostic/checkpoint lanes, replacement seed apps `3508` and `3509` attached workers and became the seventh/eighth full confirmation lanes.

Stopped to free Modal H100 task slots:

- `ap-UFX7iAhRQvOQ5NmqWCkWlc`: 3040/no-reon seed3400. Stopped after it was behind the old lead at both `1750` and `1875`.
- `ap-82jZGAorIouGJ2H084NIT8`: 3100 seed2900 checkpoint replay. Stopped because the 3000 replay is the relevant below-3000 path and the active task slots were needed for n=8 full confirmation.
- Zero-task failed shells stopped for cleanliness: `ap-ugRDej21Ml4vdugWDHuMPQ`, `ap-EMYwrk3lfa8FgHWphcjOv5`, `ap-151e6LrITcWoC2WEdOG3Ka`, `ap-KtoeNBPtciTSjbxUkNOeVe`.

Still active besides the eight full confirmation lanes:

- `ap-oJt8hUqjcUqyJINytpVyPR`: 3040/re-on-at-2800 seed3401, one task.
- `ap-aMJg05trVXsT8rfFsRkQne`: 3000 seed2900 checkpoint replay, one task; expected to save/exit at step `2500`.

Next gates:

- Full confirmation wave: first screens at `25/50/.../125`; compare early distribution against the seed2900 lead but do not overreact until at least `500/750`.
- Active seed2900 3000 checkpoint replay: wait for `1625`, then `2500` checkpoint save and volume verification.
- Re-on lane: verify no `locoprop_m_apply` from `1600` to `2799`, then verify `locoprop_m_apply step=2800` and compare `2800+` against old lead and the full confirmation wave.

Eighth live poll update, 2026-06-02 03:35 IST:

- Active app list still shows ten live H100 tasks:
  - eight full 3000 confirmation lanes: seeds `3500,3501,3502,3503,3504,3505,3508,3509`;
  - `ap-aMJg05trVXsT8rfFsRkQne`: seed2900 3000 checkpoint replay;
  - `ap-oJt8hUqjcUqyJINytpVyPR`: seed3401 3040 re-on-at-2800 diagnostic.
- Seed2900 3000 checkpoint replay update:
  - `3.49637 @1625` versus old lead `3.49718 @1625`, only `0.00081` better.
  - `3.47226 @1750` versus old lead `3.47255 @1750`, only `0.00029` better.
  - `3.44804 @1875` versus old lead `3.44775 @1875`, worse by `0.00029`.
  - Read: the strong `1500` advantage mostly faded by `1625-1875`; treat the n=8 wave as a real variance/confirmation run, not as confirmed breakout.
- Re-on diagnostic:
  - `3.50081 @1625` versus old lead `3.49718 @1625`, worse by `0.00363`.
  - `3.47756 @1750` versus old lead `3.47255 @1750`, worse by `0.00501`.
  - The intended final re-on window remains untested until step `2800`.
- Full 3000 confirmation wave early gates:

| Seed | App | `@125` | `@250` | Delta vs old lead `@250=4.11183` |
| --- | --- | ---: | ---: | ---: |
| 3500 | `ap-j32hnOwCnt9M9uKKB72dlP` | `4.65734` | `4.11251` | `+0.00068` worse |
| 3501 | `ap-NmxP7sV2WOjKj5hkG6t9A2` | `4.64204` | `4.10815` | `-0.00368` better |
| 3502 | `ap-GtJaJUQEKBK10mRwU2Fsws` | `4.64994` | `4.10913` | `-0.00270` better |
| 3503 | `ap-muw1RIwCDZ6Zs12YqyCv97` | `4.62907` | `4.10466` | `-0.00717` better |
| 3504 | `ap-yFayRAOAoYZYIhZJtCuJDx` | `4.63536` | pending | pending |
| 3505 | `ap-oUdImgIQ5ybJoA00wfgcHN` | `4.64289` | `4.10938` | `-0.00245` better |
| 3508 | `ap-8hxb2L2CCcwndbsz2kdhcX` | `4.64961` | pending | pending |
| 3509 | `ap-uJtJvlUqQjK0e6S198WFhq` | `4.65898` | pending | pending |

- Read:
  - Fast-subset `@250` is mildly encouraging: 4 of 5 reported seeds beat the old lead at `250`, with best seed3503 ahead by about `0.0072`.
  - This is not sufficient for PR confirmation because the exact seed2900 replay just faded from a `0.0066` lead at `1500` to parity by `1875`.
  - Next meaningful gates: wait for complete `@250`, then `@500/@750`; prune only if the distribution clearly falls behind.

Ninth live poll update, 2026-06-02 04:26 IST:

- The seed2900 3000 checkpoint replay landed the checkpoint:
  - `3.34642 @2500`.
  - Old seed2900 lead at `2500`: `3.34646`.
  - Delta: `0.00004` better, effectively exact parity.
  - Saved file verified in Modal volume: `track3_checkpoints/modal3000_nolate1600_pr287_locom_seed2900_step2500.pt`.
- Launched exact continuation from that checkpoint:
  - App: `ap-JEcaEpGSkzOEhSWKb2w1Az`.
  - Function call: `fc-01KT2PCRFSBGE6QZEJG7VAABQB`.
  - Launch log: `.opencode/modal_track3-resume2500-exact3000-nolate1600-pr2873065-seed2900-20260601225527.launch.log`.
  - Setting: same 3000/no-late-LocoProp/PR287-after-1600 schedule, `TRACK3_RESUME_ADVANCE_DATA=1`, `TRACK3_RESUME_RESTORE_RNG=1`, `SCREEN_VAL_EVERY=25`.
  - Verification: logs show `track3_checkpoint_loaded ... step:2500 seed:2900 val_loss:3.346419095993042` and `track3_resume_advanced_data steps:2500`.
- Full n=8 confirmation wave is no longer showing a broad lead:
  - At `500`, reported seeds were all behind old lead `3.82259`:
    - seed3500 `3.83074`
    - seed3501 `3.82585`
    - seed3502 `3.82431`
    - seed3503 `3.82543`
    - seed3505 `3.82595`
    - seed3508 `3.82703`
    - seed3509 `3.83045`
  - At `750`, mixed/near-parity:
    - seed3500 `3.71505` vs old lead `3.71019`, worse by `0.00486`.
    - seed3501 `3.71370`, worse by `0.00351`.
    - seed3502 `3.70957`, better by `0.00062`.
    - seed3503 `3.71105`, worse by `0.00086`.
    - seed3505 `3.71454`, worse by `0.00435`.
    - seed3508 `3.71028`, worse by `0.00009`.
    - seed3509 `3.71326`, worse by `0.00307`.
  - seed3504 is live but unusually slow, about `7078ms/step`, with latest raw tail around step `458`; do not use it for fast fanout decisions.
- Read:
  - The original 3000 checkpoint replay and the n=8 fanout both look like parity/noise, not a clean below-3000 PR signal.
  - Keep the exact resume to 3000, because it directly answers the seed2900 finish from the saved checkpoint.
  - Keep the n=8 fanout to `1000` unless it clearly falls behind; if it remains parity/slightly worse at `1000`, start pruning and use freed slots for suffix variants from the checkpoint.

Tenth live poll update, 2026-06-02 04:43 IST:

- Pruned one bad hardware/throughput lane:
  - `ap-yFayRAOAoYZYIhZJtCuJDx` / seed3504 was stopped with `modal app stop --yes`.
  - Reason: it was both weak and very slow. It had only reached `3.82594 @500` while running around `7078ms/step`, and logs emitted a DCGM warning (`temp_c=90 (> 89C)`).
  - This leaves seven useful full 3000 confirmation lanes active for the moment: seeds `3500,3501,3502,3503,3505,3508,3509`.
- Full 3000 fanout around the `1000-1125` gate:
  - seed3500: `3.63450 @1000`, `3.60354 @1125`; delta vs old lead at `1125` is `-0.00058`.
  - seed3501: `3.63186 @1000`, `3.60239 @1125`; delta vs old lead at `1125` is `-0.00173`.
  - seed3502: `3.63077 @1000`, `3.60465 @1125`; delta vs old lead at `1125` is `+0.00053`.
  - seed3503: `3.63341 @1000`, `3.60570 @1125`; delta vs old lead at `1125` is `+0.00158`.
  - seed3505: `3.63312 @1000`, `3.60014 @1125`; delta vs old lead at `1125` is `-0.00398`.
  - seed3508: `3.62833 @1000`; delta vs old lead at `1000` is `-0.00528`.
  - seed3509: `3.63359 @1000`; delta vs old lead at `1000` is `-0.00002`.
  - Read: still live/encouraging enough to continue, but this is not yet a broad below-3000 signal. Wait for `1250/1500`.
- Late diagnostics:
  - 3040 re-on-at-2800 lane `ap-oJt8hUqjcUqyJINytpVyPR` reached `3.29843 @2950` and `3.29674 @2975`.
  - Relative to the old lead, those are `+0.00218` at `2950` and `+0.00186` at `2975`. It improved its relative slope after re-on but remains behind, so it is unlikely to be the 3030 fix by itself.
  - Exact checkpoint resume `ap-JEcaEpGSkzOEhSWKb2w1Az` reached `3.32224 @2675` and `3.31980 @2700`, matching the old seed2900 trajectory closely.
- Suffix experiment from the seed2900 step-2500 checkpoint:
  - First attempt `ap-hBQPEKyThRiHbDmqtA3bSF` failed immediately because `TRACK3_RESUME_CHECKPOINT` was passed as the Modal-volume-relative path `track3_checkpoints/modal3000_nolate1600_pr287_locom_seed2900_step2500.pt`.
  - The training code resolves the path inside the container, so it needs the mounted absolute path `/root/.cache/track3_checkpoints/modal3000_nolate1600_pr287_locom_seed2900_step2500.pt`.
  - Corrected suffix app: `ap-BCrV8VVvIMHYXPAJL8XvDC`; function call `fc-01KT2Q7AJN0GZMFWHRAKYH0GA5`; active container `ta-01KT2Q82JAMTH7F5C5QG46CYN4`.
  - Setting: resume seed2900 from step `2500`, `TRACK3_TRAIN_STEPS=3030`, `TRACK3_LR_SCHEDULE=power`, `TRACK3_LR_POWER=0.50`, `TRACK3_LOCOM_END_STEP=1000000000`, `TRACK3_LOCOM_NORM_CAP=0.20`, `SCREEN_VAL_EVERY=25`.
  - Verification: logs show `track3_checkpoint_loaded path:/root/.cache/track3_checkpoints/modal3000_nolate1600_pr287_locom_seed2900_step2500.pt step:2500 seed:2900 val_loss:3.346419095993042` and `track3_resume_advanced_data steps:2500`.
  - First active LocoProp log at `2500` shows a much larger late base step (`base_step` about `0.97`) than the cold exact replay tail, so this directly tests whether warmer late LR plus active LocoProp fixes the slope collapse.
- Current decision:
  - Keep the seven useful full 3000 lanes alive through at least `1250/1500`.
  - Keep the exact resume through `3000`.
  - Keep the 3040 re-on lane through finish because it is close to done and gives a clean late-window read.
  - Monitor the corrected `3030/power0.50/cap0.20` suffix aggressively; if it is promising by `2750/2800`, launch the next suffix lane when a slot opens.

Eleventh live poll update, 2026-06-02 04:55 IST:

- 3040 re-on-at-2800 diagnostic `ap-oJt8hUqjcUqyJINytpVyPR` finished:
  - `3.29369 @3025`, `3.29295 @3040`.
  - It recovered relative slope after re-on, but still missed target and remained worse than the old lead tail. This is not the fix by itself.
- Exact seed2900 checkpoint resume `ap-JEcaEpGSkzOEhSWKb2w1Az` remains essentially identical to the old lead:
  - `3.30816 @2800`, `3.30597 @2825`, `3.30383 @2850`.
  - These are within a few `1e-4` of the old seed2900 reference, so the checkpoint is faithful and does not itself explain the late miss.
- Suffix experiments from the step-2500 checkpoint:
  - `3030/power0.50/cap0.20` (`ap-BCrV8VVvIMHYXPAJL8XvDC`) was stopped after immediate regression: `3.38188 @2525`, `3.38922 @2550`, about `+0.05` worse than exact. Warm power LR is too aggressive from the checkpoint.
  - `3030/pr287-switch/cap0.20` (`ap-tfE8KUbBnUcSQJQY9qhBW1`, container `ta-01KT2QMPMJPGQHH2KAK81PRYM7`) loaded correctly and is near exact so far: `3.34328 @2525`, `3.33948 @2550`, only about `+0.0003` worse than exact.
  - `3030/pr287-switch/cap0.50` (`ap-bKtqswLl39GZd9xN0d9Svn`) was stopped after early regression: `3.34941 @2525`, about `+0.0064` worse than exact.
  - Read: late LocoProp with the original LR semantics and `cap=0.20` is not dead yet; higher cap and warmer LR are both too disruptive immediately.
- Full 3000 confirmation wave:
  - The useful full lanes reached the `1250` region with modestly positive deltas:
    - seed3500: `3.57012 @1250`, `-0.00122` vs old lead.
    - seed3501: `3.57009 @1250`, `-0.00125` vs old lead.
    - seed3502: `3.56828 @1250`, `-0.00306` vs old lead.
    - seed3503: `3.56822 @1250`, `-0.00312` vs old lead.
    - seed3505: `3.57015 @1250`, `-0.00119` vs old lead.
    - seed3508/3509 lag in wall time but were also ahead at `1125`.
  - This is still not enough to claim below-3000, but it is positive enough to restore the eighth confirmation lane.
- Replacement full confirmation seed launched:
  - App: `ap-mv6wxDA8lYcaw602sMgPWr`.
  - Function call: `fc-01KT2R14M1N7NGJJBRJX27M3HF`.
  - Container: `ta-01KT2R15R94K2AH8P0ZQG95PNW`.
  - Launch log: `.opencode/modal_track3-simple-locom-3000-nolate1600-pr2873065-full-h100-seed3512-20260601232404.launch.log`.
  - Intended role: replacement for stopped slow seed3504, restoring n=8 full-run confirmation if it logs `seed=3512` cleanly.
- Current active high-value set:
  - Full 3000 confirmation lanes: seeds `3500,3501,3502,3503,3505,3508,3509`, plus replacement seed `3512` pending seed-line confirmation.
  - Exact resume: `ap-JEcaEpGSkzOEhSWKb2w1Az`, keep to final `3000`.
  - One remaining suffix: `ap-tfE8KUbBnUcSQJQY9qhBW1` (`3030/pr287-switch/cap0.20`), keep at least through `2750/2800` unless it starts diverging.

Twelfth live poll update, 2026-06-02 05:16 IST:

- Exact seed2900 checkpoint resume finished:
  - App: `ap-JEcaEpGSkzOEhSWKb2w1Az`.
  - Final: `3.29350 @3000`.
  - This is faithful to the old lead tail and slightly better than the remembered `3.29374`, but still far from `3.28`.
  - Conclusion: the checkpoint itself is good; exact continuation does not solve the late landing.
- Full 3000 confirmation wave is now materially positive at the `1500` gate:
  - seed3500: `3.51487 @1500`, `-0.00318` vs old lead.
  - seed3501: `3.51426 @1500`, `-0.00379` vs old lead.
  - seed3502: `3.51357 @1500`, `-0.00448` vs old lead.
  - seed3503: `3.51393 @1500`, `-0.00412` vs old lead.
  - seed3505 had not reached `1500` in the poll but was near lead at `1375`; seed3508/3509 were `-0.00349/-0.00198` at `1375`.
  - Replacement seed3512 is live and confirmed clean: `track3_trial_seed=3512`, with early `5.42474 @50` and `4.23843 @200`.
  - Read: this is the strongest full-wave persistence gate so far. Keep all full lanes through `1625/1750` before deciding whether this is likely sub-3000.
- Suffix results:
  - `3030/pr287-switch/cap0.20` late-LocoProp suffix (`ap-tfE8KUbBnUcSQJQY9qhBW1`) continues to track exact but not improve it:
    - `3.33584 @2575`, `3.32953 @2625`, `3.31418 @2750`, `3.31122 @2775`.
    - These are consistently about `+0.0003` to `+0.0005` worse than exact/reference.
    - Decision: keep through `2800+` only to see whether the late window changes slope; it has no evidence of a win yet.
  - `3030/pr287-switch3125/noloco` suffix (`ap-NNGZBjVn0VVSO00HWfU9wu`) was stopped:
    - `3.34584 @2525`, `3.34291 @2550`, about `+0.0037` worse by `2550`.
    - Read: extending the PR287 horizon from `2500` is too disruptive.
  - New delayed-tail LR suffix launched:
    - App: `ap-1Lzp2CU3AkUJST7kHDwxHj`.
    - Function call: `fc-01KT2S1NH32790PJ1ENEDFM98Z`.
    - Container: `ta-01KT2S1PEAQD0D6990FPM7ZP5F`.
    - Launch log: `.opencode/modal_track3-suffix-s3030-pr287tail3125-noloco-seed2900-20260601234148.launch.log`.
    - Setting: resume from step `2500`, train to `3030`, use exact PR287 schedule (`TRACK3_LR_SCHEDULE=pr287`, steps `3065`) until `step=2800`, then switch to PR287 horizon `3125`; `TRACK3_LOCOM_END_STEP=1600` so late LocoProp is off.
    - Verification: loaded `/root/.cache/track3_checkpoints/modal3000_nolate1600_pr287_locom_seed2900_step2500.pt` and matched exact at `2525`: `3.34299 @2525`.
    - Read: this is the correct tail-only LR isolation. It should match exact until `2800`; the decision point is `2825/2850+`.
- Current decision:
  - Carry all eight full confirmation lanes.
  - Carry `3030/pr287-tail3125/noloco` at least through `2850`.
  - Carry `3030/pr287-switch/cap0.20` late-LocoProp through `2800/2825`; stop it if it remains a flat `+0.0003` tracker after the late region.

Thirteenth live poll update, 2026-06-02 05:24 IST:

- Full 3000 confirmation wave:
  - The strong `1500` lead faded materially by `1625`.
  - At `1500`, mature seeds were still good:
    - seed3500 `3.51487`, `-0.00318` vs old lead.
    - seed3501 `3.51426`, `-0.00379`.
    - seed3502 `3.51357`, `-0.00448`.
    - seed3503 `3.51393`, `-0.00412`.
    - seed3505 `3.51445`, `-0.00360`.
    - seed3508 `3.51352`, `-0.00453`.
    - seed3509 `3.51518`, `-0.00287`.
  - At `1625`, the lead mostly vanished:
    - seed3500 `3.49841`, `+0.00123` worse than old lead.
    - seed3501 `3.49782`, `+0.00064`.
    - seed3502 `3.49643`, `-0.00075`.
    - seed3503 `3.49735`, `+0.00017`.
  - Read: there is a repeated pattern now: healthy mid-run lead around `1500`, then rapid fade by `1625+`. Keep the full wave alive, but this is not yet an n=8 below-3000 confirmation.
- Suffixes:
  - `3030/pr287-switch/cap0.20` late-LocoProp suffix (`ap-tfE8KUbBnUcSQJQY9qhBW1`) tracked exact through `2900` without helping:
    - `3.30847 @2800`, `3.30633 @2825`, `3.30417 @2850`, `3.30200 @2875`, `3.29988 @2900`.
    - Deltas stayed around exact/parity (`-0.00002` to `+0.00022`), so it was stopped.
  - `3030/pr287-tail3125/noloco` (`ap-1Lzp2CU3AkUJST7kHDwxHj`) is the active tail-only LR test:
    - Loaded the checkpoint and matched exact before the switch: `3.34299 @2525`, `3.33919 @2550`, `3.33553 @2575`.
    - Because it switches only at step `2800`, the real decision gate is `2825/2850+`.
  - `3030/pr287tail3125+loco2800/cap0.20` combined suffix launched:
    - App: `ap-El648AhZtBGciwe3cK922S`.
    - Function call: `fc-01KT2SKP4EPYEGPGVCE86WZSYK`.
    - Container: `ta-01KT2SNBP826GZHBB4SE2608D7`.
    - Launch log: `.opencode/modal_track3-suffix-s3030-pr287tail3125-loco2800-cap020-seed2900-20260601235125.launch.log`.
    - Setting: exact PR287 schedule through `2799`, switch to PR287 horizon `3125` at `2800`, and LocoProp active only in `0:1600,2800:3030`.
    - Verification: container logs show `track3_checkpoint_loaded ... step:2500 seed:2900 val_loss:3.346419095993042` and `step:2500/3030 val_loss:3.34642`.
- Cleanup:
  - A stale/duplicate seed3512 container appeared briefly under app `ap-mv6wxDA8lYcaw602sMgPWr`; Modal reported it was already stopped by the time `modal container stop` was attempted.
  - The real seed3512 container remained active and had reached `3.98053 @325` in the latest detailed pull.
- Current decision:
  - Carry the full wave to `1750/1875` before judging the mid-run-fade pattern.
  - Carry both active tail suffixes to at least `2825/2850`.
  - No further launches until one suffix proves useful or frees capacity.

Fourteenth live poll update, 2026-06-02 05:32 IST:

- Full 3000 confirmation wave was stopped after the `1750` persistence gate failed:
  - seed3500: `3.47542 @1750`, `+0.00287` worse than old lead.
  - seed3501: `3.47417 @1750`, `+0.00162` worse.
  - seed3502: `3.47295 @1750`, `+0.00040` worse.
  - seed3503: `3.47324 @1750`, `+0.00069` worse.
  - seed3505: `3.47351 @1750`, `+0.00096` worse.
  - seed3508/3509 had already lost their `1500` advantage by the `1625/1700` region.
  - seed3512 was a late replacement only and was stopped with the rest of the wave; it had reached `3.98053 @325`.
  - Read: the `1500` signal was real but non-persistent. This is not an n=8 below-3000 candidate as currently configured.
- Apps stopped to save H100 time:
  - `ap-j32hnOwCnt9M9uKKB72dlP`
  - `ap-NmxP7sV2WOjKj5hkG6t9A2`
  - `ap-GtJaJUQEKBK10mRwU2Fsws`
  - `ap-muw1RIwCDZ6Zs12YqyCv97`
  - `ap-oUdImgIQ5ybJoA00wfgcHN`
  - `ap-8hxb2L2CCcwndbsz2kdhcX`
  - `ap-uJtJvlUqQjK0e6S198WFhq`
  - `ap-mv6wxDA8lYcaw602sMgPWr`
- Active containers after cleanup:
  - `ap-1Lzp2CU3AkUJST7kHDwxHj`: `3030/pr287-tail3125/noloco`, container `ta-01KT2S1PEAQD0D6990FPM7ZP5F`.
  - `ap-El648AhZtBGciwe3cK922S`: `3030/pr287tail3125+loco2800/cap0.20`, container `ta-01KT2SNBP826GZHBB4SE2608D7`.
- Tail suffix status before cleanup:
  - No-Loco tail3125 matched exact through `2700`: `3.31979 @2700`, effectively exact.
  - Combined tail3125+LocoProp matched exact through `2600`: `3.33259 @2600`, effectively exact.
  - Decision: only these two remain worth carrying, because they alter the run only after the targeted `2800` tail switch.

Fifteenth live poll / final cleanup update, 2026-06-02 05:53 IST:

- Exact seed2900 checkpoint replay endpoint:
  - App: `ap-JEcaEpGSkzOEhSWKb2w1Az`.
  - Checkpoint: `/root/.cache/track3_checkpoints/modal3000_nolate1600_pr287_locom_seed2900_step2500.pt`.
  - Final: `3.29350 @3000`.
  - Read: the step-2500 checkpoint/replay path is faithful and slightly cleaner than the earlier remembered `3.29374 @3000`, but it is still far above the `3.28` target.
- `3030/pr287-tail3125/noloco` suffix failed after the targeted `2800` LR-horizon switch:
  - App: `ap-1Lzp2CU3AkUJST7kHDwxHj`.
  - It matched the exact trajectory through the switch:
    - `3.31389 @2750`
    - `3.31092 @2775`
    - `3.30814 @2800`
  - After the switch, it became worse:
    - `3.30765 @2825`, about `+0.0015` worse than exact replay `3.30597 @2825`.
    - `3.30602 @2850`, about `+0.0022` worse than exact replay `3.30383 @2850`.
    - `3.30385 @2875`, about `+0.0021` worse than exact replay `3.30170 @2875`.
  - Stopped by CLI. Read: delaying only the PR287 horizon extension to `2800` does not fix the landing; it hurts the post-switch slope.
- `3030/pr287tail3125+loco2800/cap0.20` suffix also failed immediately after activation:
  - App: `ap-El648AhZtBGciwe3cK922S`.
  - It matched exact before the switch and had the intended LocoProp activation at `2800`.
  - LocoProp diagnostics at `2800` showed low alignment for the logged layers (`cos_desc` around `0.042`, `0.059`, `0.016`, `-0.013`) and several corrections heavily cap-scaled.
  - Result:
    - `3.30814 @2800`
    - `3.30775 @2825`, about `+0.0018` worse than exact replay `3.30597 @2825`.
  - Stopped by CLI. Read: adding LocoProp back at `2800` on top of the tail LR switch does not rescue the late slope and likely worsens it immediately.
- Modal cleanup verification:
  - `modal app list` shows all owned Track 3 apps stopped with `0` tasks.
  - `modal container list` reports `Active Containers in environment: None`.
- Current conclusion:
  - No n=8 confirmation exists for this Track 3 LocoProp-M PR path.
  - The full 3000 fanout had a real-looking `1500` lead, but it faded by `1625/1750`.
  - The exact checkpoint replay landed `3.29350 @3000`, and every suffix tested from the step-2500 checkpoint either tracked exact or worsened after the intended change.
  - Do not spend another n=8 wave on this exact schedule/primitive without a new mechanism that specifically fixes the late-slope collapse after roughly `2800`.

Sixteenth follow-up screen, 2026-06-02 06:20 IST:

- Tested a materially different substrate before any new fanout: current 2026-05-09 record-source script
  (`records/track_3_optimization/results/20260509_contra_soft_muon/8634073e-2a35-4cf6-b8c4-c00d441523d8.txt`)
  plus the existing capped SGD LocoProp-M correction.
- Code provenance:
  - Commit: `a227c81` (`Support Track 3 record-source LocoProp runs`).
  - App: `ap-sM9XYK1PFwjVPmhIBjBC9d`.
  - Function call: `fc-01KT2WB4EGB3VZ7Q987WV91R6T`.
  - Setting: `TRACK3_TRAIN_STEPS=3000`, `TRACK3_PASS_TRIAL_ARG=0`, `TRACK3_SEED_OFFSET=0`,
    `TRACK3_LR_SCHEDULE=pr287`, `TRACK3_LR_POWER=1.2`, `TRACK3_LR_SCHEDULE_STEPS=3105`,
    `TRACK3_LOCOM_END_STEP=1600`, H100, `NPROC_PER_NODE=1`.
- Reference seed0 curve from the same source file:
  - `4.49820 @125`, `4.04970 @250`, `3.82109 @500`, `3.34256 @2500`, `3.27972 @3000`.
- Result:
  - `4.51945 @125`, `train_time=520.341s`, `step_avg=4162.73ms`.
  - Stopped by CLI after first screen. Modal logs confirm `Stopping app - user stopped from CLI` and `Runner terminated`.
- Diagnostics:
  - Step 2 logged negative correction alignment for the first four layers (`cos_desc=-0.057`, `-0.078`, `-0.084`, `-0.134`) while accepted remained `1`.
  - Step 10 still showed negative alignment and very large local objective blow-up (`lossK` much larger than `loss0`) with the norm cap doing the real scaling.
  - Step 125 remained mixed/weak (`cos_desc=-0.029`, `-0.048`, `0.064`, `0.014`) and was already worse than the source seed0 reference.
- Read:
  - Current-record substrate + every-step capped SGD LocoProp-M is both slower and worse at the first screen.
  - Do not fan this out. If this substrate is revisited, use a stricter accept gate such as local-loss decrease and/or nonnegative `cos_desc`, because the ungated cap-only correction is immediately dominated by overhead and bad local geometry.
