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
- Status: active detached Modal run. Verified from Modal logs: generated `/tmp/train_gpt_simple_locoprop_m_3100.py`, `steps=3100`, `mbs=16`, `track3_trial_seed=400`, owned layers `[0..11]`, step 0 validation finite at `10.82580`; latest validation reached step `2625/3100`, loss `3.34224`, with train step average near `3.66s/step`.
- Local launch log: `.opencode/modal_track3-simple-locom-3100-h100-r1-20260601.launch.log`.

Read: this is the direct 3100-step schedule variant requested after the 3350-step Prime lanes showed a slow late-cooldown slope. LocoProp-M is active from step 0 with the same K4/cap0.20 settings as the Prime lanes. At step `2000`, it is ahead of the completed Prime 3350-step seed-200/seed-300 mean (`3.44638`) by about `0.01335`. At step `2250`, it is ahead of the same Prime mean (`3.41077`) by about `0.01573`. At step `2625`, it is ahead of the same Prime mean (`3.36076`) by about `0.01851`.

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
